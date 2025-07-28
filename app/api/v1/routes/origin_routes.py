from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, abort
from app.api.v1.services.origin_service import OriginService
from app.api.v1.models.origin import OriginCreate, OriginUpdate
from pydantic import ValidationError

api = Namespace('origins', description='云盘操作')
origin_service = OriginService()


origin_fields = api.model('Origin', {
    'id': fields.String(alias='_id', description='云盘ID'),
    'name': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'size_json': fields.String(required=True, description='云盘大小', min_length=1, max_length=100),
    'count': fields.Integer(description='文件数量'),
    'bytes': fields.Integer(description='文件大小'),
    'sizeless': fields.Integer(description='文件大小'),
    'created_at': fields.DateTime(dt_format='iso8601', description='创建时间'),
    'updated_at': fields.DateTime(dt_format='iso8601', description='最后更新时间')
})

# --- 请求参数解析器 ---
list_origins_parser = reqparse.RequestParser()
list_origins_parser.add_argument('page', type=int, required=False, default=1, help='页码setDefault(1)')
list_origins_parser.add_argument('per_page', type=int, required=False, default=10, help='每页数量setDefault(10)')
list_origins_parser.add_argument('query', type=str, required=False, default='{}', help='筛选条件setDefault({})')


pagination_model = api.model('PaginatedItemResponse', {
    'items': fields.List(fields.Nested(origin_fields)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_items': fields.Integer(description='总物品数'),
    'total_pages': fields.Integer(description='总页数')
})

# --- 路由 ---
@api.route('/list')
class Origins(Resource):
    @api.doc('获取云盘列表')
    @api.expect(list_origins_parser)
    @api.marshal_list_with(pagination_model)
    def get(self):
        """获取云盘列表"""
        args = list_origins_parser.parse_args()
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        query = args.get('query', '{}')
        if isinstance(query, str):
            try:
                query = eval(query)
            except Exception as e:
                api.abort(400, f'筛选条件解析错误: {str(e)}')
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        elif per_page > 100:
            per_page = 100
        items = origin_service.query_page(query=query, page=page, per_page=per_page)
        for item in items:
            item['id'] = item.pop('_id')
        total_items = origin_service.count_items(query=query)
        total_pages = (total_items + per_page - 1) // per_page
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages
        }, 200

@api.route('/refresh')
class OriginsRefresh(Resource):
    @api.doc('刷新云盘列表')
    @api.marshal_list_with(origin_fields)
    def get(self):
        """刷新云盘列表"""
        return origin_service.refresh_origins(), 200