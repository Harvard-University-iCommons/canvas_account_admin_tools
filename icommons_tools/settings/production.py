from os.path import abspath, basename, dirname, join, normpath
from sys import path

from .base import *

DEBUG = False

ALLOWED_HOSTS = ['localdev-2.icommons.harvard.edu']

# "production" is using the dev database for now...
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isitedev',
        'USER': os.environ['DJANGO_DB_USER'],
        'PASSWORD': os.environ['DJANGO_DB_PASSWORD'],
        'HOST': 'icd3.isites.harvard.edu',
        'PORT': '8103',
        'OPTIONS': {
            'threaded': True,
        },
    }
}


STATIC_ROOT = normpath(join(SITE_ROOT, 'http_static'))

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
            'level': 'DEBUG',
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


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
