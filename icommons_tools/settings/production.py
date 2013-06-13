from os.path import abspath, basename, dirname, join, normpath
from sys import path

from .base import *

DEBUG = True

# to prevent host header poisoning 
ALLOWED_HOSTS = ['*']

'''

Configure application settings

Also Required but not set here:
DJANGO_DB_PASSWORD - must be defined in the environment
CIPHER_KEY - must be defined in the environment
ICOMMONSAPIPASS - must be defined in the environment

'''
APP_CONFIG = {
    'DJANGO_DB_HOST': 'icd3.isites.harvard.edu',
    'DJANGO_DB_PORT': '8003',
    'DJANGO_DB_SID': 'isiteqa',
    'DJANGO_DB_USER': 'termtool',
    'ICOMMONSAPIHOST': 'https://isites.harvard.edu/services/',
    'ICOMMONSAPIUSER': '2CF64ADC-4907-11E1-B318-E3828F1150F0',
    'ICOMMONSAPIPASS': os.environ['ICOMMONSAPIPASS'],
    'TERM_TOOL_LOG': '/logs/termtool/term_tool_audit.log'
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': APP_CONFIG['DJANGO_DB_SID'],
        'USER': APP_CONFIG['DJANGO_DB_USER'],
        'PASSWORD': os.environ['DJANGO_DB_PASSWORD'],
        'HOST': APP_CONFIG['DJANGO_DB_HOST'],
        'PORT': APP_CONFIG['DJANGO_DB_PORT'],
        'OPTIONS': {
            'threaded': True,
        },
    }
}


STATIC_ROOT = normpath(join(SITE_ROOT, 'http_static'))

INSTALLED_APPS += ('gunicorn',)

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
            'handlers': ['mail_admins','console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        }

    }
}


'''
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
'''
SESSION_ENGINE = 'django.contrib.sessions.backends.file'


'''
The dictionary below contains group id's and school names. 
These are the groups that are allowed to edit term informtion.
The school must be the same as the school_id in the school model.
'''

ADMIN_GROUP = 'IcGroup:25292'

ALLOWED_GROUPS = {
    'IcGroup:25096':'gse', 
    'IcGroup:25095':'fas', 
    'IcGroup:25097':'hls', 
    'IcGroup:25098':'hsph', 
    'IcGroup:25099':'hds', 
    'IcGroup:25100':'gsd', 
    'IcGroup:25101':'dce', 
    'IcGroup:25102':'hks', 
    'IcGroup:25103':'hms', 
    'IcGroup:25104':'hsdm', 
    'IcGroup:25105':'hbsmba', 
    'IcGroup:25106':'hbsdoc', 
    'IcGroup:25178':'sum' 
}

