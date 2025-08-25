#!/usr/bin/env python
"""
Script to run Celery worker and beat (scheduler) processes.
"""
import os
import sys
import time
import subprocess
from multiprocessing import Process

# Add the parent directory to sys.path so we can import from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config


def _get_app_arg():
    # Ensure correct Celery app path - use app.celery_app as default
    return getattr(Config, 'CELERY_APP', 'app.celery_app')


def _get_queues():
    # Determine queues to listen on
    manage_q = Config.TASK_QUEUE_MANAGE
    exec_q = Config.TASK_QUEUE_EXEC
    default_q = Config.CELERY_DEFAULT_QUEUE
    tasks_q = Config.CELERY_TASKS_QUEUE
    return ','.join({default_q, tasks_q, manage_q, exec_q})


def run_worker():
    """Run the Celery worker with enhanced error handling."""
    cmd = [
        'celery',
        '-A', _get_app_arg(),
        'worker',
        '--loglevel=info',
        '--concurrency', str(Config.CELERY_WORKER_CONCURRENCY),
        '--hostname', Config.CELERY_WORKER_HOSTNAME,
        '--queues', _get_queues(),
        '--max-tasks-per-child=1000',  # 防止内存泄漏
        '--time-limit=300',  # 任务超时时间（秒）
        '--soft-time-limit=240',  # 软超时时间（秒）
        '--without-gossip',  # 减少网络开销
        '--without-mingle',  # 减少启动时间
        '--without-heartbeat',  # 减少网络开销
    ]
    
    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"启动 Celery Worker (尝试 {attempt + 1}/{max_retries})")
            result = subprocess.call(cmd)
            if result == 0:
                print("Celery Worker 正常退出")
                break
            else:
                print(f"Celery Worker 异常退出，退出码: {result}")
                if attempt < max_retries - 1:
                    print(f"等待 5 秒后重试...")
                    time.sleep(5)
        except Exception as e:
            print(f"启动 Celery Worker 时发生错误: {e}")
            if attempt < max_retries - 1:
                print(f"等待 5 秒后重试...")
                time.sleep(5)
            else:
                print("达到最大重试次数，退出")
                sys.exit(1)


def run_beat():
    """Run the Celery beat (scheduler)."""
    cmd = [
        'celery',
        '-A', _get_app_arg(),
        'beat',
        '--loglevel=info',
        '--schedule', Config.CELERY_BEAT_SCHEDULE_FILE,
        '--pidfile', Config.CELERY_BEAT_PIDFILE,
    ]
    
    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"启动 Celery Beat (尝试 {attempt + 1}/{max_retries})")
            result = subprocess.call(cmd)
            if result == 0:
                print("Celery Beat 正常退出")
                break
            else:
                print(f"Celery Beat 异常退出，退出码: {result}")
                if attempt < max_retries - 1:
                    print(f"等待 5 秒后重试...")
                    time.sleep(5)
        except Exception as e:
            print(f"启动 Celery Beat 时发生错误: {e}")
            if attempt < max_retries - 1:
                print(f"等待 5 秒后重试...")
                time.sleep(5)
            else:
                print("达到最大重试次数，退出")
                sys.exit(1)


def run_flower():
    """Run the Flower monitoring tool."""
    cmd = [
        'celery',
        '-A', _get_app_arg(),
        'flower',
        '--port', str(Config.FLOWER_PORT),
        '--broker', Config.CELERY_BROKER_URL,
    ]
    subprocess.call(cmd)


def run_all():
    """Run worker, beat, and flower in separate processes."""
    processes = []

    # Start worker process
    worker_process = Process(target=run_worker)
    worker_process.start()
    processes.append(worker_process)

    # Optionally start beat process if enabled
    if Config.ENABLE_CELERY_BEAT:
        beat_process = Process(target=run_beat)
        beat_process.start()
        processes.append(beat_process)

    # Optionally start flower if enabled
    if Config.ENABLE_FLOWER:
        flower_process = Process(target=run_flower)
        flower_process.start()
        processes.append(flower_process)

    try:
        # Keep the main process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        for process in processes:
            process.terminate()
        sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'worker':
            run_worker()
        elif command == 'beat':
            run_beat()
        elif command == 'flower':
            run_flower()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_celery.py [worker|beat|flower]")
    else:
        run_all()
