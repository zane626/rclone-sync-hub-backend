from flask import Flask
from flask_restx import Api
from app.api.v1.routes.folder_routes import api as folder_ns
from app.api.v1.routes.task_routes import api as task_ns
from app.api.v1.routes.rclone_routes import api as rclone_ns
from app.api.v1.routes.info_routes import api as info_ns
from app.api.v1.routes.origin_routes import api as origin_ns
from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.utils.db import close_db_connection
import os
from flask_cors import CORS
from app.celery_app import celery, make_celery

def create_app(config_name=None):
    app = Flask(__name__)
    CORS(app)  # 默认允许所有域名访问所有路由

    # Initialize Celery
    # app.config.from_object('celery_config')
    app.config.update(
        CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0',
        CELERY_RESULT_BACKEND=os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    )
    
    # Configure Celery
    celery.conf.update(app.config)
    make_celery(app)

    if config_name == 'testing':
        app.config.from_object(TestingConfig)
    elif config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        # 默认使用开发配置，或者可以从环境变量读取
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env == 'production':
            app.config.from_object(ProductionConfig)
        elif flask_env == 'testing': # 虽然有 config_name，但这里也处理下
            app.config.from_object(TestingConfig)
        else:
            app.config.from_object(DevelopmentConfig)

    # 初始化flask-restx API
    api = Api(app, version='1.0', title='RcloneSyncHub API',
              description='RcloneSyncHub 后端接口文档，基于 Flask-RESTX 自动生成',
              doc='/api')
    # 注册命名空间
    api.add_namespace(folder_ns)
    api.add_namespace(task_ns)
    api.add_namespace(rclone_ns)
    api.add_namespace(info_ns)
    api.add_namespace(origin_ns)

    @app.route('/')
    def hello():
        return "Hello from Flask Service!"

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """在应用上下文销毁时关闭数据库连接"""
        close_db_connection() # 确保在 utils.db 中定义的 close_db_connection 被调用
    return app

if __name__ == '__main__':
    # 这部分仅用于直接运行 app.py 进行开发测试
    # 生产环境通常使用 Gunicorn 或 uWSGI
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=app.config.get('DEBUG', True))