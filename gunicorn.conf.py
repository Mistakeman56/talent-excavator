import multiprocessing

# Gunicorn 配置文件

# 绑定地址（仅监听本地，由反代对外暴露）
bind = "127.0.0.1:5001"

# Worker 进程数（CPU 核心数 × 2 + 1，单核用 2-4 即可）
workers = 4

# Worker 类型
worker_class = "sync"

# 超时时间（AI 访谈接口可能较慢，设长一些）
timeout = 120

# 最大请求数（处理这么多请求后重启 worker，防内存泄漏）
max_requests = 2000
max_requests_jitter = 200

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程名
proc_name = "talent-app"
