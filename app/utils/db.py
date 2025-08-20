from pymongo import MongoClient
from urllib.parse import urlparse
from app.config import Config

class DatabaseManager:
    """数据库连接管理类（全局共享 MongoClient，避免在 Celery 任务中依赖 Flask g）"""
    _client = None
    _db = None

    @classmethod
    def init_app(cls, app):
        """初始化Flask应用：注册应用上下文销毁时的资源清理"""
        app.teardown_appcontext(cls.close_connections)

    @classmethod
    def get_client(cls):
        """获取（或创建）全局 MongoClient 实例"""
        if cls._client is None:
            mongo_uri = Config.MONGO_URI
            cls._client = MongoClient(mongo_uri)
        return cls._client

    @classmethod
    def get_db(cls, db_name: str = None):
        """获取数据库实例，优先使用参数db_name；否则从URI中解析或使用默认库名"""
        if cls._db is None or db_name:
            client = cls.get_client()
            if db_name:
                cls._db = client[db_name]
            else:
                parsed = urlparse(Config.MONGO_URI)
                path_db = parsed.path.lstrip('/') if parsed.path else ''
                use_db = path_db if path_db else Config.MONGO_DEFAULT_DB
                cls._db = client[use_db]
        return cls._db

    @classmethod
    def get_collection(cls, collection_name: str):
        """获取指定集合"""
        db = cls.get_db()
        if not db:
            raise ConnectionError("Database connection failed")
        return db[collection_name]

    @classmethod
    def close_connections(cls, exception=None):
        """关闭数据库连接（供Flask应用上下文销毁时调用）"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

# 兼容层（逐步迁移后可移除）

def get_db(db_name: str = None):
    return DatabaseManager.get_db(db_name)


def get_collection(collection_name: str):
    return DatabaseManager.get_collection(collection_name)


def init_app(app):
    DatabaseManager.init_app(app)


def close_db_connection():
    DatabaseManager.close_connections()
