FROM python:3.10-slim

# 设置时区为亚洲/上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 先写入完整的 Debian Bookworm 源
RUN echo "deb http://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware\n\
deb http://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware\n\
deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" \
    > /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# 安装rclone
RUN curl https://rclone.org/install.sh | bash

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装Python依赖
RUN pip3 install -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    --default-timeout=1000 \
    --no-cache-dir
#RUN pip3 install -r requirements.txt

# 创建supervisor日志目录
RUN mkdir -p /var/log/supervisor

# 暴露端口
EXPOSE 5001 5555

# 启动命令 - 使用supervisord管理多个进程（gunicorn + celery worker + celery beat）
CMD ["supervisord", "-c", "/app/supervisord.conf"]