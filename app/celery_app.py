from celery import Celery
from flask import Flask
from celery.signals import worker_ready, worker_shutdown
import os

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
# app.config.from_object('celery_config')
app.config.update(
    CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0',
    CELERY_RESULT_BACKEND=os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
)

# Initialize Celery
celery = make_celery(app)

# Import tasks after celery is configured to avoid circular imports
from . import tasks  # noqa
