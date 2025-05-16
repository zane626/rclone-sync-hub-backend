import subprocess
import json
import re
import sys
from select import select
import threading
import time

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
