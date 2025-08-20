from datetime import timedelta
from celery.schedules import crontab
from app.config import Config

# Broker settings
broker_url = Config.CELERY_BROKER_URL
result_backend = Config.CELERY_RESULT_BACKEND

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
    # When enabling Celery-based initialize flow, we can schedule periodic checks here if needed.
    # These can be overridden by environment variables at runtime.
}

# Task routes
# Define two distinct logical queues: 'manage' for scanning/management and 'celery' for execution
# Default routes can be overridden by environment variables via CELERY_ config
TASK_QUEUE_MANAGE = Config.TASK_QUEUE_MANAGE
TASK_QUEUE_EXEC = Config.TASK_QUEUE_EXEC

task_routes = {
    # Management/scanning related tasks
    'task_manager.loop_check_folders': {'queue': TASK_QUEUE_MANAGE},
    # Execution/worker related tasks
    'task_manager.loop_check_task': {'queue': TASK_QUEUE_EXEC},
    # Keep previous patterns mapped to default queues for backward compatibility
    'tasks.*': {'queue': Config.CELERY_DEFAULT_QUEUE},
    'task_manager.*': {'queue': Config.CELERY_TASKS_QUEUE},
}
