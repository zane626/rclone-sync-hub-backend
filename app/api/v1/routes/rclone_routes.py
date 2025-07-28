from flask_restx import Namespace, Resource
from app.api.v1.services.rclone_service import RcloneService

api = Namespace('rclone', description='rclone操作')
rclone_service = RcloneService()

@api.route('/list')
class RcloneResource(Resource):
    @api.response(200, '获取成功')
    def get(self):
        return rclone_service.get_origin()