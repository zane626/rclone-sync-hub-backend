from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field_validation_info):
        if not ObjectId.is_valid(v):
            raise ValueError("无效的 ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type='string')


class BaseModelWithConfig(BaseModel):
    """带有通用配置的基础模型类，用于处理常见类型的JSON序列化"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str,
            PyObjectId: str
        }
        from_attributes = True  # Pydantic V2, 或在V1中使用 orm_mode = True
        populate_by_name = True  # 允许使用别名如 "_id"
