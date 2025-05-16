from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import re

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

class FolderBase(BaseModel):
    """
    文件夹基础信息
    - name: 文件夹名称
    - parent_id: 父文件夹ID (可选, 根目录则为None)
    """
    id: Optional[str] = Field(None, alias="_id", description="文件夹唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    localPath: str = Field(..., min_length=1, max_length=100, description="本地路径")
    remotePath: str = Field(..., min_length=1, max_length=100, description="远程路径")
    origin: str = Field(..., min_length=1, max_length=100, description="网盘")


    @validator('name')
    def name_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError('名称不能为空字符串')
        # 允许名称包含空格，但不能仅由空格组成
        # 可以添加更多验证规则，例如不允许特殊字符等
        return value

class FolderCreate(FolderBase):
    """用于创建文件夹的请求体"""
    pass

class FolderUpdate(BaseModel):
    """用于更新文件夹的请求体"""
    name: str = Field(..., min_length=1, max_length=100, description="文件夹名称")
    localPath: str = Field(..., min_length=1, max_length=100, description="本地路径")
    remotePath: str = Field(..., min_length=1, max_length=100, description="远程路径")
    origin: str = Field(..., min_length=1, max_length=100, description="网盘")


class Folder(FolderBase):
    """文件夹完整信息，包含数据库中的 _id 和时间戳"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间") # 创建时可以为None，更新时设置

    class Config:
        json_encoders = {
            ObjectId: str, # 将 ObjectId 序列化为字符串
            datetime: lambda dt: dt.isoformat() # 将 datetime 序列化为 ISO 格式字符串
        }
        populate_by_name = True # 允许使用字段名或别名进行赋值
        # orm_mode = True # 如果是从ORM对象转换，则需要此项，但我们直接操作字典或MongoDB文档