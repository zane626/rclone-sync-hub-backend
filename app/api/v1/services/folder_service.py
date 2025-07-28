from __future__ import annotations
from app.api.v1.models.folder import Folder
from app.api.v1.services.base_services import BaseServices

class FolderService(BaseServices):
    def __init__(self):
        super().__init__('folders')

    def check_is_exist(self, local_path: str, remote_path: str, origin: str) -> Folder | None:
        folder_data = self.collection.find_one({'localPath': local_path, 'remotePath': remote_path, 'origin': origin})
        if not folder_data:
            return None
        return Folder(**folder_data)
