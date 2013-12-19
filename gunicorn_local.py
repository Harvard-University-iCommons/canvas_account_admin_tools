import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

bind = "0.0.0.0:8001"

pidfile = 'gunicorn.pid'

accesslog = 'access.log'

errorlog = 'error.log'
