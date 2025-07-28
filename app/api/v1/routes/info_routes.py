from flask_restx import Namespace, Resource
from app.api.v1.services.info_service import InfoService

api = Namespace('info', description='其他信息')
info_service = InfoService()

@api.route('/')
class RcloneResource(Resource):
    @api.response(200, '获取成功')
    def get(self):
        return info_service.get_info()