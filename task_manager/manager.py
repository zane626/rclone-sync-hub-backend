import asyncio
import os
import time
import threading
from datetime import datetime

from models.task import TaskCreate
from task_manager.rclone_operator import check_file_exists
from utils.db import mongo_db
from task_manager.queue import TaskQueue
from utils.logger import Logger


class TaskManager:
    def __init__(self, mongo_db):
        self.mongo_db = mongo_db
        # 创建并设置当前线程的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop = asyncio.get_event_loop()
        self.logger = Logger()

    def add_task(self, task: TaskCreate):
        collection = self.mongo_db.get_collection('tasks')
        collection.insert_one(task.model_dump())

    def find_task_by_local_path(self, local_path: str):
        collection = self.mongo_db.get_collection('tasks')
        return collection.find_one({'localPath': local_path})

    def scan_directory(self, local_path, max_depth, folder_id=None, folder_name=None, remote_path='', origin=''):
        """递归扫描目录（优化版）"""
        if not os.path.exists(local_path):
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 无效路径: {local_path}")
            return

        try:
            for root, dirs, files in os.walk(local_path):
                if self.should_skip_path(root, local_path, max_depth):
                    continue

                clean_files = self.filter_hidden_files(files)
                self.process_files(root, clean_files, local_path, remote_path, origin, folder_id, folder_name)

        except PermissionError as pe:
            self.log_error(f"权限拒绝: {str(pe)}")
        except Exception as e:
            self.log_error(f"遍历异常: {str(e)}")

    def should_skip_path(self, root, base_path, max_depth):
        """判断是否跳过当前路径"""
        current_depth = root[len(base_path):].count(os.sep)
        if current_depth > max_depth:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 超过最大深度{max_depth}层，停止遍历: {root}")
            return True
        return False

    def filter_hidden_files(self, files):
        """过滤隐藏文件"""
        return [f for f in files if not f.startswith('.') and not f.endswith('~')]

    def process_files(self, root, files, local_path, remote_path, origin, folder_id, folder_name):
        """处理单个目录下的文件"""
        for file in files:
            file_path = os.path.join(root, file)
            remote_file_dir = self.build_remote_dir(file_path, local_path, remote_path)
            self.create_task_if_needed(file_path, remote_file_dir, origin, folder_id, folder_name, file)

    def build_remote_dir(self, file_path, local_path, remote_path):
        """构建远程路径"""
        relative_path = os.path.relpath(file_path, local_path)
        remote_file_path = os.path.join(remote_path, relative_path).replace('\\', '/')
        return os.path.dirname(remote_file_path)

    def get_size_format(self, file_path: str):
        size_bytes = os.path.getsize(file_path)
        """
        将字节数转换为易读的大小格式 (如 2.5MB)

        参数:
            size_bytes (int) - 文件大小（字节）

        返回:
            str - 格式化的字符串 (如 '250.00KB')
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = size_bytes

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)}{units[unit_index]}"
        else:
            return f"{size:.2f}{units[unit_index]}"

    def create_task_if_needed(self, file_path, remote_dir, origin, folder_id, folder_name, filename):
        """创建任务（如果不存在）"""
        real_path = os.path.realpath(file_path)
        if self.find_task_by_local_path(real_path):
            return

        is_has = check_file_exists(f'{origin}:{os.path.join(remote_dir, filename)}')
        task_json = {
            'localPath': real_path,
            'remotePath': remote_dir,
            'origin': origin,
            'status': 3 if is_has else 0,
            'progress': '100' if is_has else '0',
            'name': folder_name,
            'folderId': folder_id,
            'fileName': filename,
            'fileSize': self.get_size_format(file_path),
            'created_at': datetime.now(),
        }
        task_item = TaskCreate(**task_json)
        self.add_task(task_item)

    def log_error(self, message):
        """统一错误日志"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def check_folders(self, status, delay):
        collection = self.mongo_db.get_collection('folders')
        tasks_collection = self.mongo_db.get_collection('tasks')
        folders = collection.find({'status': status})
        for folder in folders:
            # 记录检测前的任务数量
            initial_tasks_count = tasks_collection.count_documents({})
            collection.update_one({'_id': folder['_id']}, {'$set': {'status': 1}})
            self.scan_directory(folder['localPath'], 10, folder['_id'], folder['name'], folder['remotePath'], folder['origin'])
            # 计算新增的任务数量
            final_tasks_count = tasks_collection.count_documents({})
            new_tasks_count = final_tasks_count - initial_tasks_count
            # 更新文件夹状态
            collection.update_one({'_id': folder['_id']}, {'$set': {'status': 2, 'lastSyncAt': datetime.now()}})
            # 添加日志记录
            self.logger.add_log({
                'name': '文件夹检测',
                'description': f'检测文件夹 {folder["name"]} ({folder["localPath"]})，新增 {new_tasks_count} 个文件任务'
            })
        self.loop.call_later(delay, self.check_folders, 0 if status == 2 else 2, delay)

    def add_task_with_delay(self, delay):
        self.loop.call_later(delay, self.check_folders, 0, delay)
        self.loop.run_forever()

value = os.environ.get('DELAY')
_delay = int(value) if value and value.isdigit() else 60 * 10

def initialize_the_project():
    print('------->初始化定时任务脚本<-------')
    '''
    TODO: 从数据库中读取delay时间
    '''
    folder_collection = mongo_db.get_collection('folders')
    task_collection = mongo_db.get_collection('tasks')
    folder_collection.update_many({'status': 1}, {'$set': {'status': 2}})
    task_collection.update_many({'status': {'$in': [1, 2]}}, {'$set': {'status': 0}})
    threading.Thread(target=loop_check_folders).start()
    threading.Thread(target=loop_check_task).start()



def loop_check_folders():
    task_manager = TaskManager(mongo_db)
    task_manager.add_task_with_delay(_delay)


def loop_check_task():
    task_queue = TaskQueue(num_threads=2)
    task_queue.add_task_with_delay(_delay)