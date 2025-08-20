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
    """Run the Celery worker."""
    cmd = [
        'celery',
        '-A', _get_app_arg(),
        'worker',
        '--loglevel=info',
        '--concurrency', str(Config.CELERY_WORKER_CONCURRENCY),
        '--hostname', Config.CELERY_WORKER_HOSTNAME,
        '--queues', _get_queues(),
    ]
    subprocess.call(cmd)


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
    subprocess.call(cmd)


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
