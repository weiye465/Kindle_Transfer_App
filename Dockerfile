# Kindle Transfer App - Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 配置阿里云镜像源加速
RUN echo "deb https://mirrors.aliyun.com/debian/ bookworm main" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security/ bookworm-security main" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main" >> /etc/apt/sources.list

# 安装基础依赖
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install -i https://mirrors.aliyun.com/pypi/simple --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads

# 设置环境变量
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app.py"]