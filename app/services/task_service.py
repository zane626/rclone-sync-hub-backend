from __future__ import annotations

from datetime import datetime
from typing import List
from bson import ObjectId
from pymongo.collection import Collection
from app.models.task import Task, TaskCreate, TaskUpdate
from app.services.base_services import BaseServices
from app.utils.db import get_db

class TaskService(BaseServices):
    def __init__(self):
        super().__init__('tasks')

    def check_is_exist(self, local_path: str, remote_path: str, origin: str) -> Task | None:
        task_data = self.collection.find_one({'localPath': local_path, 'remotePath': remote_path, 'origin': origin})
        if not task_data:
            return None
        return Task(**task_data)
