from flask import request, abort
from flask_restx import Namespace, Resource, fields, reqparse
from bson import ObjectId
from typing import List, Optional
from models.folder import Folder as FolderModel, FolderCreate as FolderCreateModel, FolderUpdate as FolderUpdateModel, PyObjectId
from services.rclone_service import RcloneService
import os
from pydantic import ValidationError

api = Namespace('rclone', description='rclone操作')
rclone_service = RcloneService()

@api.route('/')
class RcloneResource(Resource):
    @api.response(200, '获取成功')
    def get(self):
        return rclone_service.get_origin()