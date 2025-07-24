# 远程存储列表
- 列表展示当前的远程存储
- 同步按钮,点击刷新并同步远程存储的已使用空间 `rclone size aliyun: --json --fast-list`
- 每次同步任务完成后,更新远程存储的已使用空间

# 支持远程存储to远程存储的同步

# 使用celery来实现多线程任务处理
celery -A your_app worker --concurrency=4


# 监听文件夹变化
- 使用celery beat实现定时任务 可以选择周期性检测文件夹变化
- 使用watchdog实现本地文件夹变化检测
