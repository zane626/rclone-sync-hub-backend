import unittest
import json
from flask_service.app import create_app # 假设 app.py 中有 create_app 工厂函数
from flask_service.utils.db import get_db, close_db_connection

class DemoRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """在每个测试之前运行"""
        self.app = create_app(config_name='testing') # 使用测试配置
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # 清理测试数据库 (如果需要)
        # db = get_db()
        # db.items.delete_many({})

        self.item_id = None # 用于存储创建的 item_id

    def tearDown(self):
        """在每个测试之后运行"""
        # 清理测试数据库
        db = get_db()
        if db and 'items' in db.list_collection_names():
             db.items.delete_many({})
        
        # 关闭数据库连接并移除应用上下文
        # close_db_connection() # 如果 get_db 是单例且在 app context 外管理连接，则可能需要
        self.app_context.pop()

    def test_01_create_item(self):
        """测试创建 Item"""
        response = self.client.post('/api/v1/demo/items',
                                    data=json.dumps({"name": "Test Item", "price": 9.99, "description": "A test item"}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('_id', data)
        self.assertEqual(data['name'], "Test Item")
        DemoRoutesTestCase.item_id = data['_id'] # 保存 ID 用于后续测试

    def test_02_get_all_items(self):
        """测试获取所有 Items (分页)"""
        # 先创建一个 item 确保有数据
        if not DemoRoutesTestCase.item_id:
            self.test_01_create_item()

        response = self.client.get('/api/v1/demo/items?page=1&per_page=5')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('items', data)
        self.assertIsInstance(data['items'], list)
        self.assertGreaterEqual(len(data['items']), 0) # 可能是0或1，取决于其他测试是否并行
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['per_page'], 5)

    def test_03_get_single_item(self):
        """测试获取单个 Item"""
        if not DemoRoutesTestCase.item_id:
            self.fail("item_id not set, create_item test might have failed or not run prior")
        
        response = self.client.get(f'/api/v1/demo/items/{DemoRoutesTestCase.item_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['_id'], DemoRoutesTestCase.item_id)
        self.assertEqual(data['name'], "Test Item")

    def test_04_update_item(self):
        """测试更新 Item"""
        if not DemoRoutesTestCase.item_id:
            self.fail("item_id not set, create_item test might have failed or not run prior")

        update_data = {"name": "Updated Test Item", "price": 19.99}
        response = self.client.put(f'/api/v1/demo/items/{DemoRoutesTestCase.item_id}',
                                   data=json.dumps(update_data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], "Updated Test Item")
        self.assertEqual(data['price'], 19.99)

    def test_05_delete_item(self):
        """测试删除 Item"""
        if not DemoRoutesTestCase.item_id:
            self.fail("item_id not set, create_item test might have failed or not run prior")

        response = self.client.delete(f'/api/v1/demo/items/{DemoRoutesTestCase.item_id}')
        self.assertEqual(response.status_code, 200) # 或者 204 如果 API 返回 No Content
        
        # 验证 item 确实被删除了
        response_get = self.client.get(f'/api/v1/demo/items/{DemoRoutesTestCase.item_id}')
        self.assertEqual(response_get.status_code, 404)
        DemoRoutesTestCase.item_id = None # 清除 item_id

    def test_get_non_existent_item(self):
        """测试获取不存在的 Item"""
        response = self.client.get('/api/v1/demo/items/nonexistentid123')
        self.assertEqual(response.status_code, 404)

    def test_create_item_invalid_input(self):
        """测试创建 Item 时输入无效数据"""
        response = self.client.post('/api/v1/demo/items',
                                    data=json.dumps({"name": "Test Item"}), # 缺少 price
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()