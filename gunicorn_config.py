"""
Gunicorn生产环境配置
"""
import multiprocessing

# 绑定地址
bind = "0.0.0.0:5000"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 超时设置（秒）- 重要！处理大文件上传
timeout = 300  # 5分钟超时
graceful_timeout = 120
keepalive = 5

# 请求限制
max_requests = 1000
max_requests_jitter = 50

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程名称
proc_name = "kindle-transfer"

# 预加载应用
preload_app = True

# 限制请求头大小
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190