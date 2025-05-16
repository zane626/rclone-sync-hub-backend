import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
# 获取当前文件(config.py)所在的目录的父目录 (即 flask_service 目录)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DOTENV_PATH = os.path.join(BASE_DIR, '.env')

if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
else:
    print(f"Warning: .env file not found at {DOTENV_PATH}. Using default or environment-set variables.")

class Config:
    """应用配置基类"""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a_default_fallback_secret_key'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/default_db'
    # 可以添加其他通用配置

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
    MONGO_URI = os.environ.get('TEST_MONGO_URI') or 'mongodb://localhost:27017/test_db' # 使用独立的测试数据库
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