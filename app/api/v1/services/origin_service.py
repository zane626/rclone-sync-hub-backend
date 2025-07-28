from __future__ import annotations

from datetime import datetime

from app.api.v1.models.origin import Origin
from app.api.v1.services.base_services import BaseServices
from app.tasks.task_manager.rclone_operator import get_rclone_origin_list


class OriginService(BaseServices):
    def __init__(self):
        super().__init__('origins')

    def refresh_origins(self):
        origin_list = get_rclone_origin_list()
        for origin in origin_list:
            print({"name": origin['name']}, {'$set': origin})
            self.collection.update_one(
                {"name": origin['name']},  # 查找条件
                {
                    '$set': origin,
                    "$setOnInsert": {
                        "created_at": datetime.now()
                    }
                },
                upsert=True
            )
        return self.get_all_items()