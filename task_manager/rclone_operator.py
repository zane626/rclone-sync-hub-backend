import subprocess
import json
import re
import sys
import shlex
from datetime import datetime

from select import select
import threading
import time
from utils.db import mongo_db
from bson import ObjectId
from utils.logger import Logger

def get_rclone_config():
    try:
        result = subprocess.run(
            ['rclone', 'config', 'show'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        # 使用正则表达式提取[]中的内容
        matches = re.findall(r'\[(.*?)\]', result.stdout)

        return matches

    except FileNotFoundError:
        raise Exception("Rclone未安装或未添加到系统PATH")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or '未知错误'
        raise Exception(f"执行rclone命令失败: {error_msg}")
    except json.JSONDecodeError:
        raise Exception("解析rclone配置输出失败")

def check_file_exists(remote_path):
    """检查远程文件是否存在"""
    try:
        result = subprocess.run(
            ['rclone', 'lsf', remote_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        # 如果命令执行成功且有输出，说明文件存在
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        # 如果命令执行失败，说明文件不存在
        return False
    except Exception as e:
        raise Exception(f"检查文件是否存在时发生错误: {str(e)}")




class RcloneCommand:
    def __init__(self, params: dict):
        self.task_id = ObjectId(params['task_id'])
        self.other = params.get('other', '--progress --use-server-modtime --no-traverse --timeout=4h --contimeout=10m --expect-continue-timeout=10m --low-level-retries=10 --retries=5 --retries-sleep=30s')
        self.collection = mongo_db.get_collection('tasks')
        self.folder_collection = mongo_db.get_collection('folders')
        self.task = self.collection.find_one({'_id': self.task_id})
        self.last_time = time.time()
        self.created_at = self.task['created_at']
        self.logger = Logger()

    def update_fields(self, fields_to_update):
        """
        通用字段更新方法
        :param fields_to_update: 字典类型，key为字段名，value为要更新或追加的值
        :return: UpdateResult
        """
        # 构建聚合管道更新操作
        set_stage = {}
        for field, value in fields_to_update.items():
            if field == "logs":
                # 对 logs 字段特殊处理：字符串追加
                set_stage[field] = {"$concat": [{"$ifNull": [f"${field}", ""]}, value]}
            else:
                # 其他字段直接赋值
                set_stage[field] = value

        # 执行更新
        result = self.collection.update_one(
            {"_id": self.task_id},
            [{"$set": set_stage}]
        )
        return result


    def parse_rclone_flags(self):
        """
        解析 rclone 附加参数字符串为参数列表。
        :param flag_string: 例如 "--progress --timeout=4h"
        :return: ['--progress', '--timeout=4h']
        """
        try:
            return shlex.split(self.other or '')
        except ValueError as e:
            print(f"无法解析 rclone 参数字符串: {self.other!r}\n错误信息: {e}")
            return []

    def get_cmd(self):
        return ['rclone', 'copy', self.task['localPath'], f"{self.task['origin']}:{self.task['remotePath']}"] + self.parse_rclone_flags()

    @staticmethod
    def parse_rclone_progress(line):
        """
        解析rclone的进度信息
        :param line: 进度信息字符串
        :return: 解析后的进度信息字典
        """
        progress_pattern = re.compile(
            r'Transferred:\s+([\d.]+\s*\w*) / ([\d.]+\s*\w*),\s+(\d+)%,\s+([\d.]+\s*\w+/s),\s+ETA\s+([\dwdhms]+)'
        )
        match = progress_pattern.search(line)
        if match:
            return {
                'current': match.group(1),
                'total': match.group(2),
                'percent': match.group(3),
                'speed': match.group(4),
                'eta': match.group(5)
            }
        return None

    def callback(self, params, line=''):
        now = time.time()
        if now - self.last_time > 1 and params:
            self.update_fields({
                'progress': params.get('percent'),
                'speed': params.get('speed'),
                'eta': params.get('eta'),
                'current': params.get('current'),
                'total': params.get('total'),
                'logs': "\n" + line
            })
            self.last_time = now
            return
        self.update_fields({'logs': "\n" + line})

    def stream_reader(self, stream, is_error=False):
        """
        读取并解析rclone的输出流
        :param stream: 输出流
        :param is_error: 是否是错误流
        """
        for line in iter(stream.readline, ''):
            if is_error:
                sys.stderr.write(line)
                sys.stderr.flush()
                self.update_fields({'logs': "\nerror:::: " + line})
            else:
                progress = self.parse_rclone_progress(line)
                if progress:
                    self.callback(progress, line)
                sys.stdout.write(line)
                sys.stdout.flush()
        stream.close()

    def run(self):
        self.created_at = datetime.now()
        self.update_fields({'status': 2, 'startedAt': self.created_at})
        cmd = self.get_cmd()
        proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                encoding='utf-8'
            )
        # 创建独立线程读取输出流
        stdout_thread = threading.Thread(
            target=self.stream_reader,
            args=(proc.stdout, False)
        )
        stderr_thread = threading.Thread(
            target=self.stream_reader,
            args=(proc.stderr, True)
        )

        stdout_thread.start()
        stderr_thread.start()

        # 等待子进程结束
        proc.wait()

        # 确保线程完成
        stdout_thread.join()
        stderr_thread.join()

        if proc.returncode != 0:
            self.update_fields({
                'logs': f"\nRclone命令执行失败: {proc.returncode} 命令:{cmd}",
                'status': 4,
                'finishedAt': datetime.now(),
                'duration': str(datetime.now() - self.created_at),
            })
            self.logger.add_log({
                'name': '任务失败',
                'description': f'任务 {self.task['fileName']} 执行失败 耗时: {str(datetime.now() - self.created_at)} 命令: {cmd} 上传开始时间: {self.created_at} 上传结束时间: {datetime.now()}'
            })
        else:
            self.update_fields({
                'logs': '\nRclone命令执行成功',
                'status': 3,
                'finishedAt': datetime.now(),
                'duration': str(datetime.now() - self.created_at),
            })
            self.logger.add_log({
                'name': '任务完成',
                'description': f'任务 {self.task['fileName']} 已完成 耗时: {str(datetime.now() - self.created_at)}'
            })

