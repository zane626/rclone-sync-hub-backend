from datetime import datetime

from pydantic import BaseModel, Field
from typing import Optional
from app.api.v1.models.base import PyObjectId


class TaskBase(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    folderId: PyObjectId = Field(..., description="文件夹ID")
    name: Optional[str] = Field(..., min_length=1, max_length=100, description="文件夹名称")
    fileName: Optional[str] = Field(..., min_length=1, max_length=100, description="文件名称")
    localPath: Optional[str] = Field(..., min_length=1, max_length=100, description="本地路径")
    remotePath: Optional[str] = Field(..., min_length=1, max_length=100, description="远程路径")
    origin: Optional[str] = Field(..., min_length=1, max_length=100, description="网盘")
    status: Optional[int] = Field(default=0, description="任务状态, 0: 待上传, 1: 队列中, 2: 上传中, 3: 上传完成, 4: 上传失败")
    progress: Optional[str] = Field(None, description="任务进度")
    speed: Optional[str] = Field(None, description="任务速度")
    eta: Optional[str] = Field(None, description="任务预计完成时间")
    current: Optional[str] = Field(None, description="当前进度")
    total: Optional[str] = Field(None, description="总进度")
    logs: Optional[str] = Field(None, description="任务日志")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    startedAt: Optional[datetime] = Field(None, description="开始时间")
    finishedAt: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[str] = Field(None, description="用时")
    fileSize: Optional[str] = Field(None, description="文件大小")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    pass

class Task(TaskBase):
    pass