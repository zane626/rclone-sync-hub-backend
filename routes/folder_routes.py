from flask import request, abort
from flask_restx import Namespace, Resource, fields, reqparse
from bson import ObjectId
from typing import List, Optional
from models.folder import Folder as FolderModel, FolderCreate as FolderCreateModel, FolderUpdate as FolderUpdateModel, PyObjectId
from services.folder_service import FolderService

api = Namespace('folders', description='文件夹操作')
folder_service = FolderService()


folder_fields = api.model('Folder', {
    'id': fields.String(alias='_id', description='文件夹ID'),
    'name': fields.String(required=True, description='文件夹名称', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'remotePath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
    'created_at': fields.DateTime(dt_format='iso8601', description='创建时间'),
    'updated_at': fields.DateTime(dt_format='iso8601', description='最后更新时间')
})

folder_create_fields = api.model('FolderCreate', {
    'name': fields.String(required=True, description='文件夹名称', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'remotePath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
})

folder_update_fields = api.model('FolderUpdate', {
    'name': fields.String(required=True, description='文件夹名称', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='云盘名称', min_length=1, max_length=100),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'remotePath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
})

# --- 请求参数解析器 --- 
list_folders_parser = reqparse.RequestParser()
list_folders_parser.add_argument('page', type=int, required=False, default=1, help='页码，默认为1')
list_folders_parser.add_argument('per_page', type=int, required=False, default=10, help='每页数量，默认为10，最大100')
list_folders_parser.add_argument('query', type=dict, required=False, default={}, help='筛选条件')

pagination_model = api.model('PaginatedItemResponse', {
    'items': fields.List(fields.Nested(folder_fields)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_items': fields.Integer(description='总物品数'),
    'total_pages': fields.Integer(description='总页数')
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
        query = args.get('query', {})
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        elif per_page > 100:
            per_page = 100
        items = folder_service.get_all_items(query=query, page=page, per_page=per_page)
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
        data = request.json
        try:
            # Pydantic 模型验证 (Flask-RESTX 的 validate=True 也会做一些基础验证)
            folder_create_data = FolderCreateModel(**data)
        except Exception as pydantic_exc: # 更通用的 Pydantic ValidationError
            abort(400, f"请求数据校验失败: {pydantic_exc}")

        try:
            created_folder = run_async(folder_service.create_folder(folder_create_data))
            return created_folder, 201
        except LookupError as e: # 父文件夹未找到
            abort(404, str(e))
        except ValueError as e: # 名称冲突或其他验证错误
            abort(400, str(e))
        except RuntimeError as e: # 创建后无法检索
            abort(500, str(e))
        except Exception as e:
            # log.error(f"Error creating folder: {e}")
            abort(500, "创建文件夹时发生内部错误")

@api.route('/<string:folder_id>')
@api.response(404, '文件夹未找到')
@api.param('folder_id', '文件夹的ID')
class FolderResource(Resource):
    @api.doc('get_folder')
    @api.marshal_with(folder_fields)
    def get(self, folder_id):
        """获取指定ID的文件夹详情"""
        try:
            folder_id_obj = PyObjectId(folder_id)
        except ValueError:
            abort(400, f"无效的文件夹ID格式: {folder_id}")
        
        try:
            folder = run_async(folder_service.get_folder_by_id(folder_id_obj))
            if not folder:
                abort(404, "文件夹未找到")
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
        try:
            folder_id_obj = PyObjectId(folder_id)
        except ValueError:
            abort(400, f"无效的文件夹ID格式: {folder_id}")

        try:
            # Pydantic 模型验证
            folder_update_data = FolderUpdateModel(**data)
        except Exception as pydantic_exc:
            abort(400, f"请求数据校验失败: {pydantic_exc}")

        try:
            updated_folder = run_async(folder_service.update_folder(folder_id_obj, folder_update_data))
            if not updated_folder:
                abort(404, "文件夹未找到或更新失败") # 服务层可能返回None
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
            folder_id_obj = PyObjectId(folder_id)
        except ValueError:
            abort(400, f"无效的文件夹ID格式: {folder_id}")
        
        try:
            success = run_async(folder_service.delete_folder(folder_id_obj))
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
