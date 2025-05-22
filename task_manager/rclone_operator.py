import subprocess
import json
import re
import sys
from select import select
import threading
import time
from utils.db import mongo_db

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

def run_rclone(task_id):
    try:
        collection = mongo_db.get_collection('tasks')
        task = collection.find_one({'_id': task_id})
        collection.update_one({'_id': task_id}, {'$set': {'status': 2}})
        # TODO: 执行 rclone 命令
        print(task)
    except Exception as e:
        print('执行失败', e)