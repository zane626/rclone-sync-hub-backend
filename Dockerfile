FROM ubuntu:latest

# 设置时区为亚洲/上海
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装基础软件包和Python环境
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 安装rclone
RUN curl https://rclone.org/install.sh | bash

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装Python依赖
RUN pip3 install -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]