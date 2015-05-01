from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'SHOPPER_ROLE': 'Shopper',
}

EXPORT_TOOL = {
    'base_file_download_url': 'https://qa.isites.harvard.edu/exports/',
    'ssh_hostname': 'icommons@qa.isites.harvard.edu',  # name used to connect via ssh to perl script server
    'ssh_private_key': '/home/ubuntu/.ssh/id_rsa',
    'create_site_zip_cmd': '/u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl',
    'remove_site_zip_cmd': '/u02/icommons/perlapps/iSitesAPI/scripts/rm_export_file.pl',
    'archive_cutoff_time_in_hours': 2,  # express cutoff time in hours
    'archive_task_crontab_hours': "*/1",  # hourly frequency that periodic task executes in crontab format
    'allowed_groups': 'IcGroup:358',
    'local_archive_dir': '/home/ubuntu/isites_exports',
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
    'ICOMMONS_EXT_TOOLS_URL_BASE' : 'http://test.tlt.harvard.edu/ext_tools/canvas-course-site-wizard',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isitedev',
        'USER': SECURE_SETTINGS.get('django_db_user', None),
        'PASSWORD': SECURE_SETTINGS.get('django_db_pass', None),
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
        'LOCATION': 'django-qa-cache.kc9kh3.0001.use1.cache.amazonaws.com:6379',
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
    },
}

SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_HOST = 'django-qa-cache.kc9kh3.0001.use1.cache.amazonaws.com'
SESSION_REDIS_PORT = 6379

HUEY = {
    'backend': 'huey.backends.redis_backend',  # required.
    'name': 'huey-icommons_tools-test',
    'connection': {'host': 'django-qa-cache.kc9kh3.0001.use1.cache.amazonaws.com', 'port': 6379},
}

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
            'filename': '/var/opt/tlt/logs/icommons_tools.log',
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
        'canvas_whitelist': {
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


# When starting gunicorn, this setting will tell the script which config to pull
GUNICORN_CONFIG = 'gunicorn_test.py'
