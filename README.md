# SyncWatcher

[![Docker](https://img.shields.io/badge/Docker-3.0+-blue)](https://www.docker.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.3%2B-brightgreen)](https://vuejs.org)
[![Celery](https://img.shields.io/badge/Celery-5.3%2B-yellowgreen)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.0%2B-red)](https://redis.io/)

智能文件同步管理系统，基于rclone实现自动化多线程同步，提供可视化监控界面。

## ✨ 功能特性
- 文件夹实时监听（通过watchdog）
- 多线程同步任务队列
- 同步日志审计（成功/失败记录）
- Rclone配置可视化管理
- 同步策略自定义（定时/立即触发）
- 实时同步状态看板

## 🛠️ 技术栈
| 组件          | 技术选型                  |
|---------------|--------------------------|
| 后端          | FastAPI + Celery + MongoDB |
| 前端          | Vue3 + Pinia + NaiveUI   |
| 存储          | MongoDB Atlas            |
| 容器化        | Docker Compose           |

## ✅ 功能完成度

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 任务队列 | ◻️ | 生成任务并创建队列执行rclone任务 |
| 基础接口 | ◻️ | 文件夹和任务创建接口 |
| WebUI | ◻️ | 响应式界面设计 |
| 文件监听 | ◻️ | 支持本地文件夹实时监控 |
| 多线程同步 | ◻️ | 基于Celery实现并发任务处理 |
| 同步日志 | ◻️ | 记录所有同步操作及结果 |
| Rclone配置 | ◻️ | 可视化管理远程存储配置 |
| 同步策略 | ◻️ | 支持定时和手动触发 |
| 状态看板 | ◻️ | 实时展示同步任务状态 |
| Docker部署 | ◻️ | 提供容器化一键部署 |



## 🚀 快速启动
```bash
# 克隆项目
git clone https://github.com/zane626/rclone-sync-hub-backend.git
cd rclone-sync-hub-backend

# 启动服务
docker compose up --build
```

#### 使用Docker直接部署
```bash
# 构建镜像
docker build -t rclone-sync-hub-backend .

# 运行容器
docker run -d -p 5001:5001 --name rclone-sync-hub-backend rclone-sync-hub-backend
```
# 环境变量
| 环境变量 | 描述 | 默认 |
|---------|------| -----|
| MONGO_URI | MongoDB连接字符串 | mongodb://mongodb:27017/ |
| DELAY | 同步任务检查间隔(秒) | 600 |