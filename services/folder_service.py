from bson import ObjectId
from datetime import datetime
from typing import List, Optional
from utils.db import get_db
from models.folder import Folder, FolderCreate, FolderUpdate, PyObjectId


class FolderService:
    @property
    def collection(self):
        return get_db()['folders']

    def get_all_items(self, query=None, page: int = 1, per_page: int = 10) -> List[dict]:
        """
        获取 文件夹 列表，支持分页。
        """
        if query is None:
            query = {}
        skip = (page - 1) * per_page
        items_cursor = self.collection.find(query).skip(skip).limit(per_page)
        items_list = []
        for item in items_cursor:
            item['_id'] = str(item['_id'])
            items_list.append(item)
        return items_list

    def count_items(self, query=None) -> int:
        """
        计算 Item 的总数。
        """
        return self.collection.count_documents(filter=query)