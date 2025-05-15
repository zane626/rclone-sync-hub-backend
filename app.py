from flask import Flask
from flask_restx import Api
from routes.demo_routes import api as demo_ns
from routes.folder_routes import api as folder_ns # 导入新的 folder 命名空间
from config import DevelopmentConfig, TestingConfig, ProductionConfig # 假设这些配置类已定义
from utils.db import close_db_connection
import os

def create_app(config_name=None):
    app = Flask(__name__)

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
    api.add_namespace(demo_ns)
    api.add_namespace(folder_ns) # 注册 folder 命名空间

    # 可以在这里初始化其他扩展，例如 Flask-PyMongo, Flask-Login 等
    # from .utils.db import get_db
    # db = get_db() # 确保数据库连接在应用上下文中被正确处理

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