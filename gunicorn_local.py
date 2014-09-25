import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

bind = "0.0.0.0:8001"

pidfile = 'gunicorn.pid'

accesslog = 'access.log'

errorlog = 'error.log'

proc_name = 'gunicorn_icommons_tools'

secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'https', 
    'X-FORWARDED-PROTO': 'https', 
    'X-FORWARDED-SSL': 'on'
}