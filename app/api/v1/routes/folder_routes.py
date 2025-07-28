from datetime import datetime
from flask import request, abort
from flask_restx import Namespace, Resource, fields, reqparse
from app.api.v1.models.folder import FolderCreate as FolderCreateModel, FolderUpdate as FolderUpdateModel
from app.api.v1.services.folder_service import FolderService
import os
from pydantic import ValidationError

api = Namespace('folders', description='文件夹操作')
folder_service = FolderService()


folder_fields = api.model('Folder', {
    'id': fields.String(alias='_id', description='文件夹ID'),
    'name': fields.String(required=True, description='文件夹名称', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'originPath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
    'syncType': fields.String(required=True, description='同步类型', min_length=1, max_length=100),
    'remotePath': fields.String(required=True, description='目标路径', min_length=1, max_length=100),
    'maxDepth': fields.Integer(required=True, description='最大深度'),
    'uploadNum': fields.Integer(required=True, description='上传数量'),
    'created_at': fields.DateTime(dt_format='iso8601', description='创建时间'),
    'updated_at': fields.DateTime(dt_format='iso8601', description='最后更新时间')
})

folder_create_fields = api.model('FolderCreate', {
    'name': fields.String(required=True, description='文件夹名称', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'originPath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
    'syncType': fields.String(required=True, description='同步类型', min_length=1, max_length=100),
    'remotePath': fields.String(description='目标路径 ', min_length=1, max_length=100),
    'maxDepth': fields.Integer(required=True, description='最大深度'),
})

folder_update_fields = api.model('FolderUpdate', {
    'name': fields.String(required=True, description='文件夹名称', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'originPath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
    'syncType': fields.String(required=True, description='同步类型', min_length=1, max_length=100),
    'remotePath': fields.String(description='目标路径 ', min_length=1, max_length=100),
    'maxDepth': fields.Integer(required=True, description='最大深度'),
})

# --- 请求参数解析器 --- 
list_folders_parser = reqparse.RequestParser()
list_folders_parser.add_argument('page', type=int, required=False, default=1, help='页码，默认为1')
list_folders_parser.add_argument('per_page', type=int, required=False, default=10, help='每页数量，默认为10，最大100')
list_folders_parser.add_argument('query', type=str, required=False, default='{}', help='筛选条件')

pagination_model = api.model('PaginatedItemResponse', {
    'items': fields.List(fields.Nested(folder_fields)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_items': fields.Integer(description='总物品数'),
    'total_pages': fields.Integer(description='总页数')
})


folder_tree_parser = reqparse.RequestParser()
folder_tree_parser.add_argument('path', type=str, default='', location='args')


folder_tree = api.model('Folder', {
    'name': fields.String(description='名称', min_length=1, max_length=100),
    'path': fields.String(description='路径', min_length=1, max_length=100),
    'is_dir': fields.Boolean(description='是否是文件夹'),
})
folder_tree_fields = api.model('PaginatedItemResponse', {
    'children': fields.List(fields.Nested(folder_tree)),
})

@api.route('/')
class FolderList(Resource):
    @api.doc(description='文件夹分页列表')
    @api.expect(list_folders_parser)
    @api.response(200, '查询成功')
    @api.response(400, '参数错误')
    @api.marshal_list_with(pagination_model)
    def get(self):
        """获取文件夹列表"""
        args = list_folders_parser.parse_args()
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
        items = folder_service.query_page(query=query, page=page, per_page=per_page)
        for item in items:
            item['id'] = item.pop('_id')
        total_items = folder_service.count_items(query=query)
        total_pages = (total_items + per_page - 1) // per_page
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages
        }, 200

    @api.doc('create_folder')
    @api.expect(folder_create_fields, validate=True)
    @api.marshal_with(folder_fields, code=201)
    def post(self):
        """创建新文件夹"""
        try:
            json_data = request.get_json()
            if not json_data:
                api.abort(400, '请求体必须为JSON')
            now = datetime.now()
            json_data['created_at'] = now
            json_data['updated_at'] = now
            item_data = FolderCreateModel(**json_data)
        except ValidationError as e:
            api.abort(400, f'参数校验失败: {e.errors()}')
        except Exception as e:
            api.abort(400, str(e))
        is_exist = folder_service.check_is_exist(item_data.localPath, item_data.remotePath, item_data.origin)
        if is_exist is None:
            created_item = folder_service.create_item(item_data)
            if created_item:
                created_item['id'] = str(created_item['_id'])
                return created_item, 201
        else:
            api.abort(400, '文件夹已存在')
        api.abort(500, '创建失败')
        return None


@api.route('/<string:folder_id>')
@api.response(404, '文件夹未找到')
@api.param('folder_id', '文件夹的ID')
class FolderResource(Resource):
    @api.doc('get_folder')
    @api.marshal_with(folder_fields)
    def get(self, folder_id):
        """获取指定ID的文件夹详情"""
        try:
            folder = folder_service.get_item_by_id(folder_id)
            if not folder:
                abort(404, "文件夹未找到")
            folder['id'] = str(folder['_id'])
            return folder
        except ValueError as e: # 来自服务层的ID格式错误 (理论上已被上面捕获)
            abort(400, str(e))
        except Exception as e:
            # log.error(f"Error getting folder {folder_id}: {e}")
            abort(500, "获取文件夹详情时发生内部错误")

    @api.doc('update_folder')
    @api.expect(folder_update_fields, validate=True)
    @api.marshal_with(folder_fields)
    def put(self, folder_id):
        """更新指定ID的文件夹信息"""
        data = request.json
        now = datetime.now()
        data['updated_at'] = now
        try:
            # Pydantic 模型验证
            folder_update_data = FolderUpdateModel(**data)
        except Exception as pydantic_exc:
            abort(400, f"请求数据校验失败: {pydantic_exc}")

        try:
            updated_folder = folder_service.update_item(folder_id, folder_update_data)
            if not updated_folder:
                abort(404, "文件夹未找到或更新失败") # 服务层可能返回None
            updated_folder['id'] = str(updated_folder['_id'])
            return updated_folder
        except LookupError as e: # 父文件夹或自身未找到
            abort(404, str(e))
        except ValueError as e: # 名称冲突或其他验证错误
            abort(400, str(e))
        except Exception as e:
            # log.error(f"Error updating folder {folder_id}: {e}")
            abort(500, "更新文件夹时发生内部错误")

    @api.doc('delete_folder')
    @api.response(204, '文件夹已删除')
    def delete(self, folder_id):
        """删除指定ID的文件夹"""
        try:
            success = folder_service.delete_item(folder_id)
            if not success:
                # delete_folder 内部会抛出具体的异常，或者返回False
                # 如果返回False但未抛异常，这里处理
                abort(404, "文件夹未找到或删除失败")
            return '', 204
        except ValueError as e: # 例如，文件夹包含子文件夹
            abort(400, str(e))
        except Exception as e:
            # log.error(f"Error deleting folder {folder_id}: {e}")
            abort(500, "删除文件夹时发生内部错误")


@api.route('/tree')
class FolderTreeResource(Resource):
    @api.doc('获取本地文件夹树')
    @api.expect(folder_tree_parser)
    @api.response(200, '查询成功')
    @api.response(400, '参数错误')
    @api.marshal_with(folder_tree_fields)
    def get(self):
        """获取文件夹树"""
        args = folder_tree_parser.parse_args()
        path = args.get('path', '')
        # 安全校验
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(os.path.expanduser('~'), path))
        if not os.path.exists(path) or not os.path.isdir(path):
            return []
        try:
            children = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                children.append({
                    'name': item,
                    'path': full_path,
                    'is_dir': os.path.isdir(full_path)
                })
            return {'children': children}
        except Exception as e:
            return {'error': str(e)}, 500

