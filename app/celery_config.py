import os
from datetime import timedelta
from celery.schedules import crontab

# Broker settings
broker_url = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
result_backend = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True

# Task result settings
result_expires = 60 * 60 * 24  # 1 day

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100

# Beat settings (for scheduled tasks)
beat_schedule = {
    'example-periodic-task': {
        'task': 'tasks.example_periodic_task',
        'schedule': timedelta(minutes=30),
        'args': ()
    },
    # Add more scheduled tasks here
}

# Task routes
task_routes = {
    'tasks.*': {'queue': 'default'},
    'task_manager.*': {'queue': 'tasks'},
}
