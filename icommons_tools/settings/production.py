from os.path import abspath, basename, dirname, join, normpath
from sys import path

from .base import *

# debug must be false for production
DEBUG = False

# to prevent host header poisoning 
ALLOWED_HOSTS = ['*']

'''
Configure application settings

Also Required but not set here:
DJANGO_DB_PASSWORD - must be defined in the environment
DJANGO_SECRET_KEY - must be defined in the environment
CIPHER_KEY - must be defined in the environment
ICOMMONSAPIPASS - must be defined in the environment
'''

APP_CONFIG = {
    'ICOMMONSAPIHOST': 'https://isites.harvard.edu/services/',
    'ICOMMONSAPIUSER': SECURE_SETTINGS['ICOMMONS_API_USER'],
    'ICOMMONSAPIPASS': SECURE_SETTINGS['ICOMMONS_API_PASS'],
    'TERM_TOOL_LOG': '/logs/termtool/term_tool_audit.log'
}

DATABASES = {
    'default': {
        'ENGINE': 'oraclepool',
        'NAME': 'isitedgd',
        'USER': SECURE_SETTINGS['DJANGO_DB_USER'],
        'PASSWORD': SECURE_SETTINGS['DJANGO_DB_PASS'],
        'HOST': 'dbnode3.isites.harvard.edu',
        'PORT': '8003',
        'OPTIONS': {
            'threaded': True,
        },
        'CONN_MAX_AGE': 600,
    }
}

# need to override the NLS_DATE_FORMAT that is set by oraclepool
'''
DATABASE_EXTRAS = {
    'session': ["ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS' NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'", ], 
    'threaded': True
}
'''

CANVAS_API_HOSTNAME = 'canvas.harvard.edu'
CANVAS_API_BASE_URL = 'https://'+API_HOSTNAME+'/api/v1'
CANVAS_BASE_URL = 'https://'+CANVAS_API_HOSTNAME

STATIC_ROOT = normpath(join(SITE_ROOT, 'http_static'))

INSTALLED_APPS += ('gunicorn',)

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '127.0.0.1:6379',
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
    },
}

SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379

'''
Added verbose formatter and logfile handlers
'''
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(message)s'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': APP_CONFIG['TERM_TOOL_LOG'],
            'formatter': 'verbose'
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },

    }
}



SESSION_COOKIE_SECURE = True

'''
The dictionary below contains group id's and school names. 
These are the groups that are allowed to edit term informtion.
The school must be the same as the school_id in the school model.
'''

ADMIN_GROUP = 'IcGroup:25292'

ALLOWED_GROUPS = {
    'IcGroup:25096': 'gse',
    'IcGroup:25095': 'colgsas',
    'IcGroup:25097': 'hls',
    'IcGroup:25098': 'hsph',
    'IcGroup:25099': 'hds',
    'IcGroup:25100': 'gsd',
    'IcGroup:25101': 'ext',
    'IcGroup:25102': 'hks',
    'IcGroup:25103': 'hms',
    'IcGroup:25104': 'hsdm',
    'IcGroup:25105': 'hbsmba',
    'IcGroup:25106': 'hbsdoc',
    'IcGroup:25178': 'sum'
}

GUNICORN_CONFIG = 'gunicorn_prod.py'

