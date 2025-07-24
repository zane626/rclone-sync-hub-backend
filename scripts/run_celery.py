#!/usr/bin/env python
"""
Script to run Celery worker and beat (scheduler) processes.
"""
import os
import subprocess
import sys
from multiprocessing import Process

def run_worker():
    """Run the Celery worker."""
    cmd = [
        'celery',
        '-A', 'celery_app',
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--hostname=worker1@%h',
        '--queues=default,tasks',
    ]
    subprocess.call(cmd)

def run_beat():
    """Run the Celery beat (scheduler)."""
    cmd = [
        'celery',
        '-A', 'celery_app',
        'beat',
        '--loglevel=info',
        '--schedule=celerybeat-schedule',
        '--pidfile=celerybeat.pid',
    ]
    subprocess.call(cmd)

def run_flower():
    """Run the Flower monitoring tool."""
    cmd = [
        'celery',
        '-A', 'celery_app',
        'flower',
        '--port=5555',
        '--broker=redis://localhost:6379/0',
    ]
    subprocess.call(cmd)

def run_all():
    """Run worker, beat, and flower in separate processes."""
    processes = []
    
    # Start worker process
    worker_process = Process(target=run_worker)
    worker_process.start()
    processes.append(worker_process)
    
    # Start beat process
    beat_process = Process(target=run_beat)
    beat_process.start()
    processes.append(beat_process)
    
    # Start flower process
    flower_process = Process(target=run_flower)
    flower_process.start()
    processes.append(flower_process)
    
    try:
        # Keep the main process alive
        while True:
            pass
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
