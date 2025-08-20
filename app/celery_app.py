from celery import Celery
from flask import Flask
from celery.signals import worker_ready, worker_shutdown
from app.config import Config


def make_celery(app: Flask = None) -> Celery:
    """
    Create and configure a Celery instance.
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Add Flask app context to tasks
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Create a default Celery app instance for command line use
app = Flask(__name__)
# Ensure celery configuration (queues, routes, beat) is loaded
app.config.from_object('app.celery_config')
app.config.update(
    CELERY_BROKER_URL=Config.CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND=Config.CELERY_RESULT_BACKEND
)

# Initialize Celery
celery = make_celery(app)

# Import tasks after celery is configured to avoid circular imports
from . import tasks  # noqa
