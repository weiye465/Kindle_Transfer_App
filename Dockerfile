# Kindle Transfer App - 生产环境Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制并安装Python依赖（使用阿里云镜像加速）
COPY requirements.txt .
RUN pip install -i https://mirrors.aliyun.com/pypi/simple --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建上传目录和日志目录
RUN mkdir -p uploads logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5000

# 生产环境使用Gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "main:app"]