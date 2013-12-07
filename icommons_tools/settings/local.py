from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
CRISPY_FAIL_SILENTLY = not DEBUG

'''
Configure application settings

Also Required but not set here:
DJANGO_DB_PASSWORD - must be defined in the environment
DJANGO_SECRET_KEY - must be defined in the environment
CIPHER_KEY - must be defined in the environment
ICOMMONSAPIPASS - must be defined in the environment

'''
APP_CONFIG = {
    'DJANGO_DB_HOST': 'icd3.isites.harvard.edu',
    'DJANGO_DB_PORT': '8103',
    'DJANGO_DB_SID': 'isitedev',
    'DJANGO_DB_USER': 'termtool',
    'ICOMMONSAPIHOST': 'https://isites.harvard.edu/services/',
    'ICOMMONSAPIUSER': '2CF64ADC-4907-11E1-B318-E3828F1150F0',
    'ICOMMONSAPIPASS': get_env_variable('ICOMMONSAPIPASS'),
    'TERM_TOOL_LOG': '/home/vagrant/workspace/icommons_tools/term_tool.log'
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': APP_CONFIG['DJANGO_DB_SID'],
        'USER': APP_CONFIG['DJANGO_DB_USER'],
        'PASSWORD': get_env_variable('DJANGO_DB_PASSWORD'),
        'HOST': APP_CONFIG['DJANGO_DB_HOST'],
        'PORT': APP_CONFIG['DJANGO_DB_PORT'],
        'OPTIONS': {
            'threaded': True,
        },
        'CONN_MAX_AGE': 0,
    }
}

# need to override the NLS_DATE_FORMAT that is set by oraclepool

'''
DATABASE_EXTRAS = {
    'session': ["ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS' NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'", ], 
    'threaded': True
}
'''

API_HOSTNAME = 'canvas.icommons.harvard.edu'

API_BASE_URL = 'https://'+API_HOSTNAME+'/api/v1'


STATIC_ROOT = normpath(join(SITE_ROOT, 'http_static'))

INSTALLED_APPS += ('debug_toolbar','rest_framework.authtoken',)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

# For Django Debug Toolbar:
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
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
        # Log to a text file that can be rotated by logrotate
        'logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': join(SITE_ROOT, 'logs/term_tool.log'),
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
            'handlers': ['console', 'logfile'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },        
        'isites_export_tool': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'oraclepool': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'huey.consumer': {
            'handlers': ['logfile'],
            'level': 'INFO',
            'propagate': True,
        },
        'icommons_common.auth.views': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'rest_framework': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends.oracle': {
            'handlers': ['console', 'logfile'],
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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

HUEY = {
    'backend': 'huey.backends.redis_backend',  # required.
    'name': 'hueytest',
    'connection': {'host': 'localhost', 'port': 6379},
    'always_eager': False, # Defaults to False when running via manage.py run_huey

    # Options to pass into the consumer when running ``manage.py run_huey``
    'consumer_options': {'workers': 2},
}

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

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


