from __future__ import annotations
from app.utils.db import get_db
from app.tasks.task_manager.rclone_operator import get_rclone_config

class RcloneService:
    @property
    def collection(self):
        return get_db()['items']

    def get_origin(self):
        return get_rclone_config()
