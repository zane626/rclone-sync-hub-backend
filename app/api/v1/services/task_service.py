from __future__ import annotations

from app.api.v1.models.task import Task
from app.api.v1.services.base_services import BaseServices


class TaskService(BaseServices):
    def __init__(self):
        super().__init__('tasks')

    def check_is_exist(self, local_path: str, remote_path: str, origin: str) -> Task | None:
        task_data = self.collection.find_one({'localPath': local_path, 'remotePath': remote_path, 'origin': origin})
        if not task_data:
            return None
        return Task(**task_data)
