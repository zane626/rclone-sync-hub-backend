from __future__ import annotations

from datetime import datetime, timedelta

from utils.db import get_db

class InfoService:
    @property
    def items_collection(self):
        return get_db()['tasks']

    @property
    def folders_collection(self):
        return get_db()['folders']

    @property
    def log_collection(self):
        return get_db()['log']

    def get_week_analysis(self):
        # 获取当前时间并规范化到当日零点
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = today - timedelta(days=6)  # 包含今天共7天

        # 转换为ISO格式（适配MongoDB日期查询）
        date_range_start = seven_days_ago
        date_range_end = today + timedelta(days=1)  # 结束时间设为明天零点

        pipeline = [
            # 筛选 created_at 或 finished_at 在近7天的文档
            {
                "$match": {
                    "$or": [
                        {"created_at": {"$gte": date_range_start, "$lt": date_range_end}},
                        {"finishedAt": {"$gte": date_range_start, "$lt": date_range_end}}
                    ]
                }
            },
            # 提取日期并投影为字符串（如 "2025-05-15"）
            {
                "$addFields": {
                    "createdDate": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                    },
                    "finishedDate": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$finishedAt"}
                    }
                }
            },
            # 拆分文档为“新增”和“完成”两条记录（便于统计）
            {
                "$project": {
                    "events": [
                        {"type": "add", "date": "$createdDate"},
                        {"type": "success", "date": "$finishedDate"}
                    ]
                }
            },
            {"$unwind": "$events"},
            # 过滤掉日期超出范围的记录
            {
                "$match": {
                    "events.date": {
                        "$gte": seven_days_ago.strftime("%Y-%m-%d"),
                        "$lte": today.strftime("%Y-%m-%d")
                    }
                }
            },
            # 按日期和类型分组统计
            {
                "$group": {
                    "_id": {"date": "$events.date", "type": "$events.type"},
                    "count": {"$sum": 1}
                }
            },
            # 二次分组，合并 add 和 success 到同一文档
            {
                "$group": {
                    "_id": "$_id.date",
                    "add": {
                        "$sum": {"$cond": [{"$eq": ["$_id.type", "add"]}, "$count", 0]}
                    },
                    "success": {
                        "$sum": {"$cond": [{"$eq": ["$_id.type", "success"]}, "$count", 0]}
                    }
                }
            }
        ]

        # 执行聚合查询
        result = list(self.items_collection.aggregate(pipeline))

        # 生成近7天所有日期列表
        all_dates = [
            (today - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(6, -1, -1)  # 从7天前到今天的顺序
        ]

        # 将查询结果转换为按日期索引的字典
        result_dict = {item["_id"]: {"add": item["add"], "success": item["success"]} for item in result}

        # 填充缺失日期为0
        final_result = [
            {
                "date": date,
                "add": result_dict.get(date, {}).get("add", 0),
                "success": result_dict.get(date, {}).get("success", 0)
            }
            for date in all_dates
        ]

        return final_result

    def get_info(self):
        logs = self.log_collection.find({}).skip(0).limit(10)
        logs_list = []
        for item in logs:
            item['_id'] = str(item['_id'])
            logs_list.append(item)

        print(self.items_collection.count_documents({}))
        result = {
            'folders': self.folders_collection.count_documents({}),
            'uploaded': self.items_collection.count_documents({'status': 2}),
            'toBeUploaded': self.items_collection.count_documents({'status': {'$in': [0, 1]}}),
            'success': self.items_collection.count_documents({'status': 3}),
            'logs': logs_list,
            'final_result': self.get_week_analysis(),
        }
        return result