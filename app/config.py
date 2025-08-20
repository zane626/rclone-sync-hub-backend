import os
from dotenv import load_dotenv

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def load_environment_config():
    """根据环境变量自动加载对应的配置文件"""
    env = os.environ.get('FLASK_ENV', 'development').lower()
    
    # 根据环境选择配置文件
    if env == 'production':
        env_file = os.path.join(PROJECT_ROOT, '.env.prod')
    else:
        env_file = os.path.join(PROJECT_ROOT, '.env')
    
    # 加载配置文件
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"已加载配置文件: {env_file}")
    else:
        print(f"警告: 配置文件不存在 {env_file}. 将使用环境变量或默认值.")

# 加载环境配置
load_environment_config()

class ConfigManager:
    """统一配置管理器"""
    
    @staticmethod
    def get_config(key: str, default: str = None, required: bool = False):
        """获取配置值"""
        value = os.environ.get(key, default)
        if required and value is None:
            raise ValueError(f"必需的配置项 {key} 未设置")
        return value
    
    @staticmethod
    def get_bool_config(key: str, default: bool = False):
        """获取布尔类型配置值"""
        value = os.environ.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int_config(key: str, default: int = 0):
        """获取整数类型配置值"""
        try:
            return int(os.environ.get(key, str(default)))
        except ValueError:
            return default

class Config:
    """应用配置基类"""
    # Flask 核心配置
    SECRET_KEY = ConfigManager.get_config('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = ConfigManager.get_bool_config('FLASK_DEBUG', False)
    
    # 数据库配置
    MONGO_URI = ConfigManager.get_config('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DEFAULT_DB = ConfigManager.get_config('MONGO_DEFAULT_DB', 'rclone')
    
    # Celery 配置
    CELERY_BROKER_URL = ConfigManager.get_config('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = ConfigManager.get_config('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # 任务队列配置
    TASK_QUEUE_MANAGE = ConfigManager.get_config('TASK_QUEUE_MANAGE', 'manage')
    TASK_QUEUE_EXEC = ConfigManager.get_config('TASK_QUEUE_EXEC', 'celery')
    CELERY_DEFAULT_QUEUE = ConfigManager.get_config('CELERY_DEFAULT_QUEUE', 'default')
    CELERY_TASKS_QUEUE = ConfigManager.get_config('CELERY_TASKS_QUEUE', 'tasks')
    
    # Celery Worker 配置
    CELERY_WORKER_CONCURRENCY = ConfigManager.get_int_config('CELERY_WORKER_CONCURRENCY', 4)
    CELERY_WORKER_HOSTNAME = ConfigManager.get_config('CELERY_WORKER_HOSTNAME', 'worker1@%h')
    
    # Celery Beat 配置
    CELERY_BEAT_SCHEDULE_FILE = ConfigManager.get_config('CELERY_BEAT_SCHEDULE_FILE', 'celerybeat-schedule')
    CELERY_BEAT_PIDFILE = ConfigManager.get_config('CELERY_BEAT_PIDFILE', 'celerybeat.pid')
    
    # Flower 配置
    FLOWER_PORT = ConfigManager.get_int_config('FLOWER_PORT', 5555)
    ENABLE_CELERY_BEAT = ConfigManager.get_bool_config('ENABLE_CELERY_BEAT', True)
    ENABLE_FLOWER = ConfigManager.get_bool_config('ENABLE_FLOWER', False)
    
    # 任务管理配置
    TASK_RUN_MODE = ConfigManager.get_config('TASK_RUN_MODE', 'celery')
    DELAY = ConfigManager.get_int_config('DELAY', 600)
    
    print('当前配置 MONGO_URI =====>', MONGO_URI)
    print('当前配置 CELERY_BROKER_URL =====>', CELERY_BROKER_URL)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 开发环境特有的配置，例如更详细的日志

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境特有的配置，例如不同的数据库URI或日志级别

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    # 使用独立的测试数据库，通过ConfigManager读取避免硬编码
    MONGO_URI = ConfigManager.get_config('TEST_MONGO_URI', 'mongodb://localhost:27017/test_db')
    # 测试环境特有的配置

# 根据 FLASK_ENV 环境变量选择配置
config_name = os.environ.get('FLASK_ENV', 'development').lower()

if config_name == 'production':
    app_config = ProductionConfig()
elif config_name == 'testing':
    app_config = TestingConfig()
else:
    app_config = DevelopmentConfig()

# 打印加载的配置以供调试 (可选)
# print(f"Loading config: {config_name}")
# print(f"MONGO_URI: {app_config.MONGO_URI}")