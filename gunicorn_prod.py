import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

'''
Point to local apache 
'''
bind = "127.0.0.1:8183"
#bind = "10.35.1.56:8183"

#daemon = True

pidfile = '/logs/icommons_tools/gunicorn.pid'

accesslog = '/logs/icommons_tools/gunicorn_access.log'

errorlog = '/logs/icommons_tools/gunicorn_error.log'

proc_name = 'gunicorn_icommons_tools'
