import logging
from app.celery_app import celery
from datetime import datetime
from app.config import Config

logger = logging.getLogger(__name__)

# 单例占位符：在任务函数内进行延迟初始化，避免导入时创建线程/事件循环
_task_manager_singleton = None
_task_queue_singleton = None

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
        from app.utils.db import DatabaseManager
        task_manager = TaskManager(DatabaseManager.get_db())
        
        # Call your existing sync method
        result = task_manager.sync_files(task_id, source_path, destination_path, **kwargs)
        
        # Update task status to completed
        TaskService.update_task_status(task_id, 'completed', result=result)
        
        return {"status": "success", "task_id": task_id, "result": result}
    except Exception as e:
        logger.error(f"Error in sync_task {task_id}: {str(e)}")
        TaskService.update_task_status(task_id, 'failed', error=str(e))
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

@celery.task(bind=True, name='task_manager.loop_check_folders')
def celery_loop_check_folders(self, delay=None):
    """
    Celery任务包装器：处理文件夹检测
    此任务调用现有的TaskManager来处理文件夹扫描，保持原有逻辑不变
    """
    # 解析延迟：优先使用参数，否则从配置获取
    if delay is None:
        delay = Config.DELAY

    # 队列名称从配置读取
    manage_queue = Config.TASK_QUEUE_MANAGE

    try:
        logger.info(f"运行文件夹检测任务，延迟: {delay}秒，队列: {manage_queue}")
        
        # 局部实例化 TaskManager，避免事件循环句柄累积
        from app.tasks.task_manager.manager import TaskManager
        from app.utils.db import DatabaseManager
        task_manager = TaskManager(DatabaseManager.get_db())

        # 执行检测（单次）
        task_manager.check_folders(0, delay)  # 检测状态为0的文件夹
        
        return {"status": "success", "message": f"文件夹检测任务完成，延迟: {delay}秒"}
    except Exception as e:
        logger.error(f"文件夹检测任务执行失败: {str(e)}")
        # 失败场景交由Celery自身重试逻辑处理，避免重复调度
        raise self.retry(exc=e, countdown=300)  # 5分钟后重试
    finally:
        # 关闭 TaskManager 的事件循环，避免未运行的 call_later 任务在内存中累积
        try:
            tm = locals().get('task_manager')
            if tm and getattr(tm, 'loop', None):
                try:
                    tm.loop.close()
                except Exception:
                    pass
        except Exception:
            pass
        # 注意：定时调度现在由Celery Beat处理，不需要自我调度

@celery.task(bind=True, name='task_manager.loop_check_task')  
def celery_loop_check_task(self, delay=None):
    """
    Celery任务包装器：处理任务队列执行
    此任务保持原有逻辑不变，但避免向事件循环注册延迟回调导致的内存累积
    """
    # 解析延迟：优先使用参数，否则从配置获取
    if delay is None:
        delay = Config.DELAY

    exec_queue = Config.TASK_QUEUE_EXEC

    global _task_queue_singleton
    if _task_queue_singleton is None:
        try:
            from app.tasks.task_manager.queue import TaskQueue
            _task_queue_singleton = TaskQueue(num_threads=2)
        except Exception as e:
            logger.error(f"TaskQueue 单例初始化失败: {e}")
            raise

    try:
        logger.info(f"运行任务队列检测，延迟: {delay}秒，队列: {exec_queue}")
        
        # 直接执行一次性的队列填充逻辑，避免在事件循环中注册延迟回调
        from app.utils.db import DatabaseManager
        collection = DatabaseManager.get_collection('tasks')
        tasks_cursor = collection.find({'status': 0})
        added = 0
        for task in tasks_cursor:
            _task_queue_singleton.add_task(str(task['_id']))
            collection.update_one({'_id': task['_id']}, {'$set': {'status': 1}})
            added += 1
        logger.info(f"本次扫描加入队列的任务数: {added}")
        
        return {"status": "success", "message": f"任务队列检测完成，延迟: {delay}秒，新增: {added}"}
    except Exception as e:
        logger.error(f"任务队列检测执行失败: {str(e)}")
        raise self.retry(exc=e, countdown=300)  # 5分钟后重试
    finally:
        # 注意：定时调度现在由Celery Beat处理，不需要自我调度
