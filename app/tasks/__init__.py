import logging
from app.celery_app import celery
from datetime import datetime

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='tasks.example_periodic_task')
def example_periodic_task(self):
    """
    Example periodic task that runs every 30 minutes
    """
    try:
        logger.info(f"Running example periodic task at {datetime.now()}")
        # Add your task logic here
        return {"status": "success", "message": "Task completed successfully"}
    except Exception as e:
        logger.error(f"Error in example_periodic_task: {str(e)}")
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds

@celery.task(bind=True, name='tasks.sync_task')
def sync_task(self, task_id, source_path, destination_path, **kwargs):
    """
    Task to handle file synchronization
    """
    try:
        logger.info(f"Starting sync task {task_id}: {source_path} -> {destination_path}")
        
        # Update task status in database
        from app.api.v1.services import TaskService
        TaskService.update_task_status(task_id, 'in_progress')
        
        # Here you would implement the actual sync logic
        # For example, using your existing task_manager
        from app.tasks.task_manager.manager import TaskManager
        task_manager = TaskManager()
        
        # Call your existing sync method
        result = task_manager.sync_files(task_id, source_path, destination_path, **kwargs)
        
        # Update task status to completed
        TaskService.update_task_status(task_id, 'completed', result=result)
        
        return {"status": "success", "task_id": task_id, "result": result}
    except Exception as e:
        logger.error(f"Error in sync_task {task_id}: {str(e)}")
        TaskService.update_task_status(task_id, 'failed', error=str(e))
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
