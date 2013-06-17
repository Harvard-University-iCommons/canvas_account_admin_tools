import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

'''
Point to local apache 
'''
bind = "127.0.0.1:8183"
#bind = "10.35.1.56:8183"

daemon = True

pidfile = 'gunicorn.pid'

accesslog = 'access.log'

errorlog = 'error.log'
