from datetime import datetime

from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List


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

class TaskBase(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    localPath: Optional[str] = Field(..., min_length=1, max_length=100, description="本地路径")
    remotePath: Optional[str] = Field(..., min_length=1, max_length=100, description="远程路径")
    origin: Optional[str] = Field(..., min_length=1, max_length=100, description="网盘")
    status: Optional[int] = Field(None, description="任务状态")
    progress: Optional[str] = Field(None, description="任务进度")
    speed: Optional[str] = Field(None, description="任务速度")
    eta: Optional[str] = Field(None, description="任务预计完成时间")
    current: Optional[str] = Field(None, description="当前进度")
    total: Optional[str] = Field(None, description="总进度")
    logs: Optional[str] = Field(None, description="任务日志")
    createdAt: datetime = Field(default_factory=datetime.now, description="创建时间")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass

class Task(TaskBase):
    pass