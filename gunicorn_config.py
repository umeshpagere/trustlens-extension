import os

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Worker processes
# A common recommendation is 2-4 x $(NUM_CORES)
workers = 2

# Threads per worker
threads = 4

# Worker timeout
# Azure OpenAI calls might take time, so we set a generous timeout
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
