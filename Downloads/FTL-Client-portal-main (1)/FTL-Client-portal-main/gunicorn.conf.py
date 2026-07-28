import multiprocessing

# Gunicorn configuration file
# Setup for high performance and stability as per architecture guide

# Bind to localhost or 0.0.0.0
bind = "0.0.0.0:8000"

# Workers calculation: (2 * CPU Cores) + 1
workers = (2 * multiprocessing.cpu_count()) + 1

# Gevent for async I/O handling, or gthread if sync views are heavy
worker_class = "gthread"
threads = 4

# Connections and timeouts
worker_connections = 1000
timeout = 30
keepalive = 5

# Memory leak accumulation prevention
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
