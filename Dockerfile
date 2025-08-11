# Kindle Transfer App - 极简Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制并安装Python依赖（使用阿里云镜像加速）
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