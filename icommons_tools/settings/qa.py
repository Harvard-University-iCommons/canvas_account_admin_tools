from .base import *

DEBUG = False

ALLOWED_HOSTS = ['termtool-qa.icommons.harvard.edu']

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
    'TERM_TOOL_LOG': 'term_tool.log'
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isiteqa',
        'USER': SECURE_SETTINGS['DJANGO_DB_USER'],
        'PASSWORD': SECURE_SETTINGS['DJANGO_DB_PASS'],
        'HOST': 'icd3.isites.harvard.edu',
        'PORT': '8003',
        'OPTIONS': {
            'threaded': True,
        },
        'CONN_MAX_AGE': 1200,
    }
}

# need to override the NLS_DATE_FORMAT that is set by oraclepool
'''
DATABASE_EXTRAS = {
    'session': ["ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS' NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'", ], 
    'threaded': True
}
'''

CANVAS_API_HOSTNAME = 'harvard.test.instructure.com'
CANVAS_API_BASE_URL = 'https://'+CANVAS_API_HOSTNAME+'/api/v1'
CANVAS_BASE_URL = 'https://'+CANVAS_API_HOSTNAME

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

SESSION_COOKIE_SECURE = True

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
        # Log to a text file that can be rotated by logrotate
        'logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': APP_CONFIG['TERM_TOOL_LOG'],
            'formatter': 'verbose'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'canvas_shopping': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'isites_export_tool': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'qualtrics_whitelist': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'qualtrics_taker_auth': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'icommons_common': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        }

    }
}


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
    'IcGroup:25178': 'sum',
}

BASE_ISITES_EXPORT_FILE_DOWNLOAD_URL = 'https://qa.isites.harvard.edu/exports/'

GUNICORN_CONFIG = 'gunicorn_qa.py'

EXPORT_TOOL = {
    'base_file_download_url' : 'https://qa.isites.harvard.edu/exports/', 
    'ssh_hostname' : 'icommons@qa.isites.harvard.edu', # name used to connect via ssh to perl script server
    'ssh_private_key' : '/home/ubuntu/.ssh/id_rsa',
    'create_site_zip_cmd' : '/u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl',
    'remove_site_zip_cmd' : '/u02/icommons/perlapps/iSitesAPI/scripts/rm_export_file.pl',
    'archive_cutoff_time_in_hours' : 2, # express cutoff time in hours
    'archive_task_crontab_hours' : "*/1", # hourly frequency that periodic task executes in crontab format
}
