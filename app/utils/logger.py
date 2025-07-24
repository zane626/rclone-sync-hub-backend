from datetime import datetime

from app.utils.db import mongo_db


class Logger:
    def __init__(self):
        self.collection = mongo_db.get_collection('log')

    def add_log(self, log: dict):
        log['created_at'] = datetime.now()
        self.collection.insert_one(log)

