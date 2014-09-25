import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

bind = "127.0.0.1:8001"

# pidfile = 'gunicorn.pid'

accesslog = '/var/opt/tlt/logs/gunicorn-icommons_tools-access.log'

errorlog = '/var/opt/tlt/logs/gunicorn-icommons_tools-error.log'

proc_name = 'gunicorn_icommons_tools'
