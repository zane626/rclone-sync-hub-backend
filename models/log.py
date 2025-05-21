from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import re
from models.base import PyObjectId


class LogBase(BaseModel):
    id: Optional[str] = Field(None, alias="_id", description="唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="日志名称")
    description: Optional[str] = Field(None, max_length=500, description="日志")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class Log(LogBase):
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        populate_by_name = True

    @validator('name')
    def name_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError('名称不能为空字符串')
        return value

class LogInDBBase(LogBase):
    """数据库中的物品基础信息"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True # Pydantic V2, or orm_mode = True for V1
        populate_by_name = True # Allows using alias like "_id"
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class LogResponse(LogInDBBase):
    """用于API响应的物品模型"""
    pass

class PaginatedLogResponse(BaseModel):
    """分页响应模型"""
    total_items: int
    total_pages: int
    current_page: int
    per_page: int
    items: List[LogResponse]