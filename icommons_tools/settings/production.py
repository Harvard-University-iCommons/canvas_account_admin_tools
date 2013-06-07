from os.path import abspath, basename, dirname, join, normpath
from sys import path

from .base import *

DEBUG = False

# to prevent host header poisoning 
ALLOWED_HOSTS = ['*']

# "production" is using the dev database for now...
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isitedev',
        'USER': 'coursemanager',
        'PASSWORD': os.environ['DJANGO_DB_PASSWORD'],
        'HOST': 'icd3.isites.harvard.edu',
        'PORT': '8103',
        'OPTIONS': {
            'threaded': True,
        },
    }
}


STATIC_ROOT = normpath(join(SITE_ROOT, 'http_static'))

INSTALLED_APPS += ('gunicorn',)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
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
ALLOWED_GROUPS = {
    
    'IcGroup:15281': 'hsph', 
    'IcGroup:2235': 'fas', 
    'IcGroup:6769': 'hds'
}

