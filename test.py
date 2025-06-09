from pymongo import MongoClient


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

mongo_db = MongoDatabase('mongodb://101.226.22.83:17027', 'rclone')
log = mongo_db.get_collection('log')
log.insert_one({'name': 'test', 'description': '测试日志'})