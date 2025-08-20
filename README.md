# Rclone Sync Hub Backend

智能文件同步管理系统的后端服务，基于 Flask + Celery + MongoDB + Redis 构建，整合 rclone 实现多源存储间的高可靠同步。提供任务编排、定时调度、状态监控与审计日志等能力，并支持容器化一键部署。

- 后端框架：Flask、Flask-RESTX
- 任务队列：Celery（Redis 作为 Broker 与 Result Backend）
- 数据存储：MongoDB
- 同步引擎：rclone
- 进程管理：supervisord（容器内同时启动 Gunicorn、Celery Worker、Celery Beat）

前端项目地址（Web 控制台）：https://github.com/zane626/rclone-sync-hub-frontend

---

## 1. 项目功能说明

- 文件夹监听与同步任务生成
  - 支持管理本地/远程文件夹源，生成对应的同步任务
  - 任务状态流转与重试策略，支持失败重试
- 任务队列与并发执行
  - Celery Worker 并发处理任务；任务按队列分流（默认 manage/celery 队列）
  - 可通过环境变量调整队列名称和并发度
- 定时调度与自调度循环
  - Celery Beat 定时触发；部分任务具备自我调度（apply_async 延时重排）能力
- 同步日志与审计
  - 记录任务执行过程、结果与错误信息，便于问题定位与回溯
- 配置管理
  - rclone 配置文件挂载/持久化；支持多远程端点管理
- API 接口
  - 基于 Flask-RESTX 暴露 REST API（/api 文档），供前端使用

端口与组件：
- 5001：后端 API（Gunicorn）
- 6379：Redis（Broker/Result）
- 27017：MongoDB
- 5555：Flower（可选，任务监控 UI）

---

## 2. 完整的使用指南

你可以选择“本地开发模式（推荐）”或“容器化运行模式”。

### 2.1 本地开发模式（Windows/PowerShell）

1) 启动 Mongo 与 Redis（使用 Docker）
```
docker compose up -d mongodb redis
```

2) 创建虚拟环境并安装依赖
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3) 设置环境变量（指向本机 Docker 暴露端口）
```
$env:FLASK_APP = "app"
$env:FLASK_ENV = "development"
$env:MONGO_URI = "mongodb://localhost:27017/rclone"
$env:CELERY_BROKER_URL = "redis://localhost:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
```

4) 启动 Flask 开发服务器
```
flask run --host=0.0.0.0 --port=5001
```

5) 新开终端启动 Celery Worker（监听多队列）
```
.\.venv\Scripts\Activate.ps1
celery -A app.celery_app worker --loglevel=info --concurrency=4 --queues=default,tasks,manage,celery
```

6) 再开终端启动 Celery Beat（定时调度）
```
.\.venv\Scripts\Activate.ps1
celery -A app.celery_app beat --loglevel=info
```

7) 可选：启动 Flower（监控界面 http://localhost:5555）
```
.\.venv\Scripts\Activate.ps1
celery -A app.celery_app flower --port=5555
```

访问后端接口与文档：
- http://localhost:5001/
- http://localhost:5001/api

### 2.2 容器化运行（Docker Compose，一键启动）

项目内置 docker-compose.yml，包含 mongodb、redis 与 backend 服务定义。

快速启动：
```
# 使用已有远程镜像标签启动
# 如需使用本地构建镜像，请参考 2.3

docker compose up -d
```

启动后：
- 后端 API： http://localhost:5001/
- （如需）将 Flower 加入到 supervisord 或单独启动一个容器运行 Flower

### 2.3 容器化运行（本地构建镜像）

Dockerfile 已改为使用 supervisord 同时托管：Gunicorn + Celery Worker + Celery Beat。

```
# 构建镜像
docker build -t rclone-sync-hub-backend:local .

# 确保本机已有 Redis 与 Mongo（可通过 compose 方式拉起）
docker compose up -d mongodb redis

# 运行容器（将服务端口映射出来）
docker run --rm -it \
  -p 5001:5001 -p 5555:5555 \
  -e FLASK_ENV=production \
  -e MONGO_URI="mongodb://host.docker.internal:27017/rclone" \
  -e CELERY_BROKER_URL="redis://host.docker.internal:6379/0" \
  -e CELERY_RESULT_BACKEND="redis://host.docker.internal:6379/0" \
  rclone-sync-hub-backend:local
```

---

## 3. 环境变量说明

- MONGO_URI：MongoDB 连接串（默认示例：mongodb://localhost:27017/rclone 或 docker-compose 中的 mongodb 服务）
- CELERY_BROKER_URL：Celery Broker（Redis）URL（默认：redis://localhost:6379/0）
- CELERY_RESULT_BACKEND：Celery Result Backend（Redis）URL（默认：redis://localhost:6379/0）
- 任务队列名称（可选）：在 app/celery_config.py 可配置 task_routes，将不同任务路由到 manage、celery 等队列；同时确保 Worker 的 --queues 参数包含对应队列

如需自定义并发、队列或调度频率，请同时检查：
- supervisord.conf（Celery Worker/Beat 启动参数）
- app/celery_app.py、app/celery_config.py（路由、调度与配置）

---

## 4. 与前端联调

前端项目地址：
- https://github.com/zane626/rclone-sync-hub-frontend

前端启动后，将 API_URL 指向后端地址（例如 http://localhost:5001），即可进行联调与功能验证。

---

## 5. 常见问题（FAQ）

- 看不到任务执行？
  - 确认 Celery Worker 已启动并且监听了 manage、celery 等队列
  - 确认 Redis 与 MongoDB 服务已正常运行
- Flower 没有显示任务？
  - 确认 Worker 正在处理相同的 Broker/Backend；刷新页面或重启 Flower
- Windows 本地开发建议使用 Flask Dev Server（flask run），Gunicorn 建议在容器或 WSL 中使用

---

## 6. 目录结构（简要）

- app/
  - api/ …… REST 接口
  - tasks/ …… Celery 任务与任务管理器
  - celery_app.py …… Celery 应用工厂与初始化
  - celery_config.py …… Celery 路由与调度配置
  - config.py …… Flask 配置
- supervisord.conf …… 统一托管 Gunicorn/Worker/Beat
- docker-compose.yml …… 一键启动所需服务
- Dockerfile …… 生产/测试构建脚本（内置 supervisord）