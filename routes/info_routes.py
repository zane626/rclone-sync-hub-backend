from flask import request, abort
from flask_restx import Namespace, Resource, fields, reqparse
from bson import ObjectId
from typing import List, Optional
from services.info_service import InfoService
import os
from pydantic import ValidationError

api = Namespace('info', description='其他信息')
info_service = InfoService()

@api.route('/')
class RcloneResource(Resource):
    @api.response(200, '获取成功')
    def get(self):
        return info_service.get_info()