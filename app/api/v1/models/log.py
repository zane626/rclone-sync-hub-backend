from pydantic import Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.api.v1.models.base import PyObjectId, BaseModelWithConfig


class LogBase(BaseModelWithConfig):
    id: Optional[str] = Field(None, alias="_id", description="唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="日志名称")
    description: Optional[str] = Field(..., description="日志")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

class Log(LogBase):
    pass

    @validator('name')
    def name_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError('名称不能为空字符串')
        return value

class LogInDBBase(LogBase):
    """数据库中的物品基础信息"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

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