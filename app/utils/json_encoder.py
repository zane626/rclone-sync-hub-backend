from datetime import datetime
import json
from bson import ObjectId

class CustomJSONEncoder(json.JSONEncoder):
    """
    自定义JSON编码器，用于处理特殊类型的序列化
    - datetime: 转换为ISO格式字符串
    - ObjectId: 转换为字符串
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)