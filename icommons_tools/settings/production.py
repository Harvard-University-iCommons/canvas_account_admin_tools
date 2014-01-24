from os.path import abspath, basename, dirname, join, normpath
from sys import path

from .base import *

import os

os.environ['http_proxy'] = 'http://10.34.5.254:8080'
os.environ['https_proxy'] = 'http://10.34.5.254:8080'

# debug must be false for production
DEBUG = False

# to prevent host header poisoning 
ALLOWED_HOSTS = ['*']

ICOMMONS_COMMON = {
    'ICOMMONS_API_HOST': 'https://isites.harvard.edu/services/',
    'ICOMMONS_API_USER': SECURE_SETTINGS['ICOMMONS_API_USER'],
    'ICOMMONS_API_PASS': SECURE_SETTINGS['ICOMMONS_API_PASS'],
    'CANVAS_API_BASE_URL': 'https://harvard.instructure.com/api/v1',
    'CANVAS_API_HEADERS': {'Authorization': 'Bearer ' + SECURE_SETTINGS['CANVAS_TOKEN']},
}

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': 'https://canvas.harvard.edu',
}

EXPORT_TOOL = {
    'base_file_download_url': 'https://qa.isites.harvard.edu/exports/', 
    'ssh_hostname': 'icommons@qa.isites.harvard.edu',  # name used to connect via ssh to perl script server
    'ssh_private_key': '/home/ubuntu/.ssh/id_rsa',
    'create_site_zip_cmd': '/u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl',
    'remove_site_zip_cmd': '/u02/icommons/perlapps/iSitesAPI/scripts/rm_export_file.pl',
    'archive_cutoff_time_in_hours': 2,  # express cutoff time in hours
    'archive_task_crontab_hours': "*/1",  # hourly frequency that periodic task executes in crontab format
}

TERM_TOOL = {
    'ADMIN_GROUP': 'IcGroup:25292',
    'ALLOWED_GROUPS': {
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
    },
}

QUALTRICS_TAKER_AUTH = {
    'QUALTRICS_API_KEY': SECURE_SETTINGS['QUALTRICS_API_KEY'],
    'BITLY_ACCESS_TOKEN': SECURE_SETTINGS['BITLY_ACCESS_TOKEN'],
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
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
            'filename': '/logs/icommons_tools/icommons_tools.log',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'course_shopping': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'qualtrics_taker_auth': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'qualtrics_whitelist': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'isites_export': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'huey': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'ERROR',
            'propagate': True,
        },

    }
}


SESSION_COOKIE_SECURE = True

GUNICORN_CONFIG = 'gunicorn_prod.py'
