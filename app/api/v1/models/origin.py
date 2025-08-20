from datetime import datetime

from pydantic import Field
from typing import Optional
from app.api.v1.models.base import BaseModelWithConfig, PyObjectId

"""
{
  "共有{count}个对象，其中全部成功获取了大小（{sizeless}个无法获取大小）",
  "总容量为 {bytes}"
}
"""
class OriginBase(BaseModelWithConfig):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100, description="云盘名称")
    size_json: str = Field(..., min_length=1, max_length=100, description="云盘大小")
    count: int = Field(default=-1, description="文件数量")
    bytes: int = Field(default=-1, description="文件大小")
    sizeless: int = Field(default=-1, description="文件大小")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="最后更新时间")


class OriginCreate(OriginBase):
    pass

class OriginUpdate(OriginBase):
    pass

class Origin(OriginBase):
    pass