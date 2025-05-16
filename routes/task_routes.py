from datetime import datetime
from pydoc import describe

from flask_restx import Namespace, Resource, fields, reqparse
from flask import request, abort
from bson import ObjectId
from services.task_service import TaskService
from models.task import TaskCreate, TaskUpdate
from pydantic import ValidationError

api = Namespace('tasks', description='任务相关操作')
task_service = TaskService()


task_model = api.model('Task', {
    'id': fields.String(alias='_id', description='任务ID'),
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'remotePath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='网盘', min_length=1, max_length=100),
    'status': fields.Integer(description='任务状态'),
    'progress': fields.String(description='任务进度'),
    'speed': fields.String(description='任务速度'),
    'eta': fields.String(description='任务预计完成时间'),
    'current': fields.String(description='当前进度'),
    'total': fields.String(description='总进度'),
    'logs': fields.String(description='任务日志'),
    'createdAt': fields.DateTime(dt_format='iso8601', description='创建时间'),
    'startedAt': fields.DateTime(dt_format='iso8601', description='开始时间'),
    'finishedAt': fields.DateTime(dt_format='iso8601', description='完成时间'),
})

task_create_model = api.model('TaskCreate', {
    'localPath': fields.String(required=True, description='本地路径', min_length=1, max_length=100),
    'remotePath': fields.String(required=True, description='远程路径', min_length=1, max_length=100),
    'origin': fields.String(required=True, description='网盘', min_length=1, max_length=100),
})

task_update_model = api.model('TaskUpdate', {
    'status': fields.Integer(description='任务状态'),
    'progress': fields.Float(description='任务进度'),
    'speed': fields.String(description='任务速度'),
    'eta': fields.String(description='任务预计完成时间'),
    'current': fields.String(description='当前进度'),
    'total': fields.String(description='总进度'),
    'logs': fields.String(description='任务日志'),
    'startedAt': fields.DateTime(dt_format='iso8601', description='开始时间'),
    'finishedAt': fields.DateTime(dt_format='iso8601', description='完成时间'),
})

# --- 请求参数解析器 ---
list_tasks_parser = reqparse.RequestParser()
list_tasks_parser.add_argument('page', type=int, required=False, default=1, help='页码，默认为1')
list_tasks_parser.add_argument('per_page', type=int, required=False, default=10, help='每页数量，默认为10，最大100')
list_tasks_parser.add_argument('query', type=str, required=False, default='{}', help='筛选条件')

pagination_model = api.model('PaginatedItemResponse', {
    'items': fields.List(fields.Nested(task_model)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_items': fields.Integer(description='总物品数'),
    'total_pages': fields.Integer(description='总页数')
})

@api.route('/')
class TaskList(Resource):
    @api.doc('任务分页列表')
    @api.expect(list_tasks_parser)
    @api.response(200, '查询成功')
    @api.response(400, '参数错误')
    @api.marshal_list_with(pagination_model)
    def get(self):
        """列出所有任务"""
        # Implement logic to retrieve tasks
        args = list_tasks_parser.parse_args()
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
        items = task_service.query_page(query=query, page=page, per_page=per_page)
        total_items = task_service.count_items(query=query)
        total_pages = (total_items + per_page - 1) // per_page
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages
        }, 200

    @api.doc('创建任务')
    @api.expect(task_create_model, validate=True)
    @api.marshal_with(task_model, code=201)
    def post(self):
        """创建新任务"""
        try:
            json_data = request.get_json()
            now = datetime.now()
            if not json_data:
                api.abort(400, '请求体必须为JSON')
            item_data = TaskCreate(**json_data)
        except ValidationError as e:
            api.abort(400, f'参数校验失败: {e.errors()}')
        except Exception as e:
            api.abort(400, str(e))
        is_exist = task_service.check_is_exist(item_data.localPath, item_data.remotePath, item_data.origin)
        if is_exist is None:
            created_item = task_service.create_item(item_data)
            if created_item:
                return created_item, 201
        else:
            api.abort(400, '任务已存在')
        api.abort(500, '创建失败')
        return None

@api.route('/<string:task_id>')
class TaskResource(Resource):
    @api.doc('获取任务详情')
    @api.marshal_with(task_model)
    def get(self, task_id):
        """获取任务详情"""
        try:
            folder = task_service.get_item_by_id(task_id)
            if not folder:
                abort(404, "文件夹未找到")
            return folder
        except ValueError as e: # 来自服务层的ID格式错误 (理论上已被上面捕获)
            abort(400, str(e))
        except Exception as e:
            # log.error(f"Error getting folder {folder_id}: {e}")
            abort(500, "获取文件夹详情时发生内部错误")

    @api.doc('更新任务信息')
    @api.expect(task_update_model)
    @api.marshal_with(task_model)
    def put(self, task_id):
        """更新任务"""
        data = request.json
        try:
            # Pydantic 模型验证
            folder_update_data = TaskUpdate(**data)
        except Exception as pydantic_exc:
            abort(400, f"请求数据校验失败: {pydantic_exc}")

        try:
            updated_folder = task_service.update_item(task_id, folder_update_data)
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

    @api.doc('删除任务')
    @api.response(204, '任务已删除')
    def delete(self, task_id):
        """删除任务"""
        try:
            success = task_service.delete_item(task_id)
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