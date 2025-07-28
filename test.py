import subprocess
import re
import json


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



def get_origin_size(origin_id):
    try:
        '''
            rclone size aliyun: --json --fast-list
        '''
        print(' '.join(['rclone', 'size', origin_id + ':', '--json', '--fast-list']))
        result = subprocess.run(
            ['rclone', 'size', origin_id + ':', '--json', '--fast-list'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        return result.stdout

    except FileNotFoundError:
        raise Exception("Rclone未安装或未添加到系统PATH")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or '未知错误'
        raise Exception(f"执行rclone命令失败: {error_msg}")
    except json.JSONDecodeError:
        raise Exception("解析rclone配置输出失败")



def get_origin_files(origin_path, max_depth):
    '''
     > rclone lsjson aliyun: --max-depth 3 --files-only
    '''
    try:
        result = subprocess.run(
            ['rclone', 'lsjson', origin_path, '--max-depth', str(max_depth), '--files-only'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        try:
            return json.loads(result.stdout)
        except Exception as e:
            raise Exception(f"执行rclone命令失败: {e}")

    except FileNotFoundError:
        raise Exception("Rclone未安装或未添加到系统PATH")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or '未知错误'
        raise Exception(f"执行rclone命令失败: {error_msg}")
    except json.JSONDecodeError:
        raise Exception("解析rclone配置输出失败")
if __name__ == "__main__":
    rclone_list = get_origin_files('aliyun:backup/', 3)
    print(rclone_list)
