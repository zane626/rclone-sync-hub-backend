from pydantic import Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import re
from app.api.v1.models.base import PyObjectId, BaseModelWithConfig

# Pydantic 对 ObjectId 的支持需要自定义类型或转换
# 我们可以使用 Annotated 和 BeforeValidator 来处理 ObjectId
# 或者在模型外部处理转换


class ItemBase(BaseModelWithConfig):
    """
    物品基础信息
    - id: 物品唯一标识
    - name: 物品名称
    - description: 物品描述
    - price: 物品价格，必须大于0
    """
    id: Optional[str] = Field(None, alias="_id", description="物品唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="物品名称")
    description: Optional[str] = Field(None, max_length=500, description="物品描述")
    price: float = Field(..., gt=0, description="物品价格，必须大于0")

class Item(ItemBase):
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")

    @validator('name')
    def name_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError('名称不能为空字符串')
        return value

class ItemCreate(ItemBase):
    """用于创建物品的请求体"""
    pass

class ItemUpdate(BaseModel):
    """用于更新物品的请求体"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="物品名称")
    description: Optional[str] = Field(None, max_length=500, description="物品描述")
    price: Optional[float] = Field(None, gt=0, description="物品价格，必须大于0")

    @validator('name', pre=True, always=True)
    def name_must_not_be_empty_if_provided(cls, value):
        if value is not None and not value.strip():
            raise ValueError('名称如果提供，则不能为空字符串')
        return value

class ItemInDBBase(ItemBase):
    """数据库中的物品基础信息"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")

    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        allow_population_by_field_name = True
        from_attributes = True # Pydantic V2, or orm_mode = True for V1
        populate_by_name = True # Allows using alias like "_id"
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class ItemResponse(ItemInDBBase):
    """用于API响应的物品模型"""
    pass

class PaginatedItemResponse(BaseModel):
    """分页响应模型"""
    total_items: int
    total_pages: int
    current_page: int
    per_page: int
    items: List[ItemResponse]