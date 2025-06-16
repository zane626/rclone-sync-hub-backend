import os
from pymongo import MongoClient
from flask import current_app, g

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_NAME = 'rclone'

class DatabaseManager:
    """数据库连接管理类"""
    _client = None
    _db = None

    @classmethod
    def init_app(cls, app):
        """初始化Flask应用"""
        app.teardown_appcontext(cls.close_connections)

    @classmethod
    def get_client(cls):
        """获取MongoClient实例（连接池）"""
        if not cls._client:
            cls._client = MongoClient(MONGO_URI + MONGO_NAME, maxPoolSize=100)
        return cls._client

    @classmethod
    def get_db(cls):
        """获取数据库实例"""
        if 'db' not in g:
            client = cls.get_client()
            db_name = current_app.config['MONGO_URI'].split('/')[-1].split('?')[0]
            if not db_name:
                db_name = current_app.config.get('MONGO_DEFAULT_DB', 'default_flask_db')
            g.db = client[db_name]
        return g.db

    @classmethod
    def get_collection(cls, collection_name):
        """获取指定集合"""
        db = cls.get_db()
        if not db:
            raise ConnectionError("Database connection failed")
        return db[collection_name]

    @classmethod
    def close_connections(cls, exception=None):
        """关闭数据库连接"""
        if cls._client:
            cls._client.close()
            cls._client = None

# 兼容层（逐步迁移后移除）
def get_db():
    return DatabaseManager.get_db()

def get_collection(collection_name):
    return DatabaseManager.get_collection(collection_name)

def init_app(app):
    DatabaseManager.init_app(app)

def close_db_connection():
    DatabaseManager.close_connections()

def close_db(e=None):
    """关闭数据库连接."""
    db = g.pop('db_client', None) # MongoClient 实例应该被存储和关闭
    # PyMongo 的 MongoClient 实例管理连接池，通常不需要显式关闭每个请求后的连接。
    # client.close() 会关闭所有套接字并停止监控线程。
    # 如果你指的是 g.db (数据库对象)，它不是直接关闭的。
    # 你应该关闭 MongoClient 实例。

    # 正确的做法是在应用上下文中管理 MongoClient 实例
    # 这里我们假设 g.db 是数据库对象，而不是客户端。
    # 通常，我们会在应用关闭时关闭 MongoClient。
    # 对于每个请求，我们从 g 中获取数据库对象，不需要每次都关闭。

    # 如果你的 get_db() 每次都创建新的 MongoClient，那么需要关闭它
    # 但更好的做法是共享 MongoClient 实例
    pass # 暂时留空，因为 MongoClient 通常在应用级别管理

def init_app(app):
    """在 Flask 应用中注册数据库关闭处理."""
    app.teardown_appcontext(close_db)
    # 可以在这里进行其他数据库相关的初始化，例如创建索引
    # with app.app_context():
    #     db = get_db()
    #     # 示例：为 items 集合的 name 字段创建唯一索引
    #     if db is not None:
    #         try:
    #             items_collection = db.items
    #             items_collection.create_index("name", unique=True, background=True)
    #             print("Created index on 'items.name'")
    #         except Exception as e:
    #             print(f"Error creating index on 'items.name': {e}")
    #     else:
    #         print("Database connection not available for index creation.")

# 示例：获取特定集合的函数
def get_collection(collection_name):
    db = get_db()
    if db is None:
        # 处理无法获取数据库连接的情况
        raise ConnectionError("Failed to connect to the database.")
    return db[collection_name]


class MongoDatabase:
    """不使用 Flask 上下文的 MongoDB 数据库操作类."""

    def __init__(self, mongo_uri, db_name):
        self.mongo_uri = mongo_uri
        self.db_name = db_name

    def get_collection(self, collection_name):
        """获取指定集合."""
        client = MongoClient(self.mongo_uri)
        db = client[self.db_name]
        return db[collection_name]

mongo_db = MongoDatabase(MONGO_URI, MONGO_NAME)
