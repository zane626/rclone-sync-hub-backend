from flask_restx import Namespace, Resource, fields, reqparse
from models.item import Item
from flask import request
from services.item_service import ItemService
from models.item import ItemCreate, ItemUpdate
from pydantic import ValidationError

api = Namespace('demo', description='Demo 相关接口')
item_service = ItemService()

parser = reqparse.RequestParser()
parser.add_argument('page', type=int, required=False, default=1, help='页码，默认为1')
parser.add_argument('per_page', type=int, required=False, default=10, help='每页数量，默认为10，最大100')
item_model = api.model('Item', {
    'name': fields.String(required=True, description='物品名称', min_length=1, max_length=100),
    'description': fields.String(required=False, description='物品描述', max_length=500),
    'price': fields.Float(required=True, description='物品价格，必须大于0', min=0.01)
})
item_update_model = api.model('ItemUpdate', {
    'name': fields.String(required=False, description='物品名称', min_length=1, max_length=100),
    'description': fields.String(required=False, description='物品描述', max_length=500),
    'price': fields.Float(required=False, description='物品价格，必须大于0', min=0.01)
})
item_response_model = api.inherit('ItemResponse', item_model, {
    'id': fields.String(description='物品ID', alias='_id'),
    'created_at': fields.DateTime(description='创建时间'),
    'updated_at': fields.DateTime(description='更新时间')
})
pagination_model = api.model('PaginatedItemResponse', {
    'items': fields.List(fields.Nested(item_response_model)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_items': fields.Integer(description='总物品数'),
    'total_pages': fields.Integer(description='总页数')
})

@api.route('/items')
class ItemResource(Resource):
    @api.expect(item_model)
    @api.response(201, '创建成功', model=item_response_model)
    @api.response(400, '请求参数错误')
    @api.doc(description='创建一个新的物品')
    def post(self):
        """创建物品"""
        try:
            json_data = request.get_json()
            if not json_data:
                api.abort(400, '请求体必须为JSON')
            item_data = ItemCreate(**json_data)
        except ValidationError as e:
            api.abort(400, f'参数校验失败: {e.errors()}')
        except Exception as e:
            api.abort(400, str(e))
        created_item = item_service.create_item(item_data)
        if created_item:
            return serialize_item(created_item), 201
        api.abort(500, '创建失败')

    @api.expect(parser)
    @api.marshal_with(pagination_model)
    @api.response(200, '查询成功')
    @api.response(400, '参数错误')
    @api.doc(description='分页获取物品列表')
    def get(self):
        """获取物品列表（分页）"""
        args = parser.parse_args()
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        elif per_page > 100:
            per_page = 100
        items = item_service.get_all_items(page=page, per_page=per_page)
        total_items = item_service.count_items()
        total_pages = (total_items + per_page - 1) // per_page
        return {
            'items': [serialize_item(item) for item in items],
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages
        }, 200

@api.route('/items/<string:item_id>')
@api.param('item_id', '物品ID')
class ItemDetailResource(Resource):
    @api.marshal_with(item_response_model)
    @api.response(200, '查询成功')
    @api.response(404, '未找到')
    @api.doc(description='根据ID获取物品详情')
    def get(self, item_id):
        """获取物品详情"""
        item = item_service.get_item_by_id(item_id)
        if item:
            return serialize_item(item), 200
        api.abort(404, '未找到该物品')

    @api.expect(item_update_model)
    @api.marshal_with(item_response_model)
    @api.response(200, '更新成功')
    @api.response(404, '未找到')
    @api.response(400, '参数错误')
    @api.doc(description='根据ID更新物品')
    def put(self, item_id):
        """更新物品"""
        try:
            json_data = request.get_json()
            if not json_data:
                api.abort(400, '请求体必须为JSON')
            item_data = ItemUpdate(**json_data)
        except ValidationError as e:
            api.abort(400, f'参数校验失败: {e.errors()}')
        except Exception as e:
            api.abort(400, str(e))
        updated_item = item_service.update_item(item_id, item_data)
        if updated_item:
            return serialize_item(updated_item), 200
        api.abort(404, '未找到或更新失败')

    @api.response(200, '删除成功')
    @api.response(404, '未找到')
    @api.doc(description='根据ID删除物品')
    def delete(self, item_id):
        """删除物品"""
        if item_service.delete_item(item_id):
            return {'message': '删除成功'}, 200
        api.abort(404, '未找到或删除失败')


def serialize_item(item):
    if isinstance(item, Item):
        return item.dict(by_alias=True)
    if isinstance(item, dict):
        item = item.copy()
        item['id'] = str(item.pop('_id', None))
        if 'created_at' in item:
            item['created_at'] = item['created_at'].isoformat()
    return item