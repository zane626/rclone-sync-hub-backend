from __future__ import annotations

from bson import ObjectId
from datetime import datetime
from utils.db import get_db
from models.item import ItemCreate, ItemUpdate # 假设 ItemUpdate 用于更新时的数据结构

class ItemService:
    def __init__(self):
        pass

    @property
    def collection(self):
        return get_db()['items']

    def create_item(self, item_data: ItemCreate) -> dict:
        """
        创建新的 Item。
        """
        now = datetime.now()
        item_doc = item_data.model_dump()
        item_doc['created_at'] = now
        item_doc['updated_at'] = now
        result = self.collection.insert_one(item_doc)
        created_item = self.collection.find_one({"_id": result.inserted_id})
        if created_item:
            created_item['_id'] = str(created_item['_id'])
        return created_item

    def get_item_by_id(self, item_id: str) -> dict | None:
        """
        根据 ID 获取单个 Item。
        """
        try:
            obj_id = ObjectId(item_id)
        except Exception:
            return None
        item = self.collection.find_one({"_id": obj_id})
        if item:
            item['_id'] = str(item['_id'])
        return item

    def get_all_items(self, page: int = 1, per_page: int = 10) -> list[dict]:
        """
        获取 Item 列表，支持分页。
        """
        skip = (page - 1) * per_page
        items_cursor = self.collection.find().skip(skip).limit(per_page)
        items_list = []
        for item in items_cursor:
            item['_id'] = str(item['_id'])
            items_list.append(item)
        return items_list

    def update_item(self, item_id: str, item_data: ItemUpdate) -> dict | None:
        """
        更新指定的 Item。
        """
        try:
            obj_id = ObjectId(item_id)
        except Exception:
            return None

        update_data = item_data.model_dump(exclude_unset=True) # 只更新提供的字段
        if not update_data:
            # 如果没有提供任何更新数据，可以考虑返回当前项或特定错误
            current_item = self.get_item_by_id(item_id)
            return current_item
            
        update_data['updated_at'] = datetime.utcnow()

        result = self.collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        if result.matched_count > 0:
            updated_item = self.collection.find_one({"_id": obj_id})
            if updated_item:
                updated_item['_id'] = str(updated_item['_id'])
            return updated_item
        return None

    def delete_item(self, item_id: str) -> bool:
        """
        删除指定的 Item。
        """
        try:
            obj_id = ObjectId(item_id)
        except Exception:
            return False
        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0

    def count_items(self) -> int:
        """
        计算 Item 的总数。
        """
        return self.collection.count_documents({})