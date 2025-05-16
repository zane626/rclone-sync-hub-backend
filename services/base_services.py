from utils.db import get_db
from bson import ObjectId

class BaseServices:
    def __init__(self, collection_name):
        self.collection_name = collection_name

    @property
    def collection(self):
        return get_db()[self.collection_name]

    def query_page(self, query=None, page: int = 1, per_page: int = 10):
        """
        分页查询
        """
        if query is None:
            query = {}
        if 'id' in query:
            query['_id'] = ObjectId(query.pop('id'))
        skip = (page - 1) * per_page
        items_cursor = self.collection.find(query).skip(skip).limit(per_page)
        items_list = []
        for item in items_cursor:
            item['_id'] = str(item['_id'])
            items_list.append(item)
        return items_list

    def create_item(self, item_data, other_data=None):
        """
        创建新的 Item
        """
        item_doc = item_data.model_dump()
        if other_data is not None:
            item_doc.update(other_data)
        result = self.collection.insert_one(item_doc)
        created_item = self.collection.find_one({"_id": result.inserted_id})
        if created_item:
            created_item['_id'] = str(created_item['_id'])
        return created_item

    def get_item_by_id(self, item_id):
        """
        查询指定的 Item
        """
        try:
            obj_id = ObjectId(item_id)
        except Exception:
            return None
        item = self.collection.find_one({"_id": obj_id})
        if item:
            item['_id'] = str(item['_id'])
        return item

    def update_item(self, item_id, item_data, other_data=None):
        """
        更新指定的 Item
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
        if other_data is not None:
            update_data.update(other_data)
        result = self.collection.update_one({"_id": obj_id}, {"$set": update_data})
        if result.matched_count == 0:
            raise LookupError("Task not found")
        updated_item = self.collection.find_one({"_id": obj_id})
        if updated_item:
            updated_item['_id'] = str(updated_item['_id'])
        return updated_item

    def delete_item(self, item_id):
        """
        删除指定的 Item
        """
        try:
            obj_id = ObjectId(item_id)
        except Exception:
            return None
        result = self.collection.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            raise LookupError("Task not found")
        return True

    def count_items(self, query=None):
        if query is None:
            query = {}
        if 'id' in query:
            query['_id'] = ObjectId(query.pop('id'))
        return self.collection.count_documents(filter=query)