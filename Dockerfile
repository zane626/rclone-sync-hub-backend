FROM python:3.10-slim

# 设置时区为亚洲/上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    --default-timeout=1000

# 复制项目文件
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=app
ENV FLASK_ENV=production

# 创建日志目录
RUN mkdir -p /var/log/supervisor

# 复制supervisor配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 5001

# 启动命令
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]