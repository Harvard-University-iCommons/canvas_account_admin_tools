from .base import *

DEBUG = True

ALLOWED_HOSTS = ['termtool-test.icommons.harvard.edu']

'''
Configure application settings
'''
APP_CONFIG = {
    'ICOMMONSAPIHOST': 'https://isites.harvard.edu/services/',
    'ICOMMONSAPIUSER': SECURE_SETTINGS['ICOMMONS_API_USER'],
    'ICOMMONSAPIPASS': SECURE_SETTINGS['ICOMMONS_API_PASS'],
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isitedev',
        'USER': SECURE_SETTINGS['DJANGO_DB_USER'],
        'PASSWORD': SECURE_SETTINGS['DJANGO_DB_PASS'],
        'HOST': 'icd3.isites.harvard.edu',
        'PORT': '8103',
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

CANVAS_API_HOSTNAME = 'canvas.icommons.harvard.edu'
CANVAS_API_BASE_URL = 'https://'+CANVAS_API_HOSTNAME+'/api/v1'
CANVAS_BASE_URL = 'https://'+CANVAS_API_HOSTNAME

INSTALLED_APPS += (
    'gunicorn',
)


# For Django Debug Toolbar:
'''
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = ('127.0.0.1','10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
'''

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
            'filename': join(SITE_ROOT, 'logs/icommons_tools.log'),
            'formatter': 'verbose',
            'level': 'DEBUG',
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
        'icommons_common': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'canvas_shopping': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },


    }
}

'''
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'django-cache.kc9kh3.0001.use1.cache.amazonaws.com:11211',
    }
}
'''


'''
The dictionary below contains group ids and school names. 
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

# When starting gunicorn, this setting will tell the script which config to pull
GUNICORN_CONFIG = 'gunicorn_test.py'

EXPORT_TOOL = {
    'base_file_download_url' : 'https://qa.isites.harvard.edu/exports/', 
    'ssh_hostname' : 'icommons@qa.isites.harvard.edu', # name used to connect via ssh to perl script server
    'ssh_private_key' : '/home/ubuntu/.ssh/id_rsa',
    'create_site_zip_cmd' : '/u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl',
    'remove_site_zip_cmd' : '/u02/icommons/perlapps/iSitesAPI/scripts/rm_export_file.pl',
    'archive_cutoff_time_in_hours' : 2, # express cutoff time in hours
    'archive_task_crontab_hours' : "*/1", # hourly frequency that periodic task executes in crontab format
}

