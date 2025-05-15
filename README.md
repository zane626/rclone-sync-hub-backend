# SyncWatcher

[![Docker](https://img.shields.io/badge/Docker-3.0+-blue)](https://www.docker.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.3%2B-brightgreen)](https://vuejs.org)

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
| 文件监听 | ◻️ | 支持本地文件夹实时监控 |
| 多线程同步 | ◻️ | 基于Celery实现并发任务处理 |
| 同步日志 | ◻️ | 记录所有同步操作及结果 |
| Rclone配置 | ◻️ | 可视化管理远程存储配置 |
| 同步策略 | ◻️ | 支持定时和手动触发 |
| 状态看板 | ◻️ | 实时展示同步任务状态 |
| WebUI | ◻️ | 响应式界面设计 |
| Docker部署 | ◻️ | 提供容器化一键部署 |
| Rclone配置生成向导 | ◻️ | 可视化remote创建向导 |
| 带宽智能调控 | ◻️ | 时间段自动限速功能 |
| 同步链路加密 | ◻️ | 集成rclone crypt功能 |
| 批量任务管理 | ◻️ | JSON/YAML格式导入导出 |
| 质量报告系统 | ◻️ | 传输成功率与速度分析 |



## 🚀 快速启动
```bash
# 克隆项目
git clone https://github.com/yourname/syncwatcher.git
cd syncwatcher

# 启动服务
docker-compose up --build

# 访问界面
http://localhost:8080