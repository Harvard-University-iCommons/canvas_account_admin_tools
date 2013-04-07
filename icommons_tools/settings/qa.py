from .base import *

DEBUG = False




DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isiteqa',
        'USER': os.environ['DJANGO_DB_USER'],
        'PASSWORD': os.environ['DJANGO_DB_PASSWORD'],
        'HOST': 'icd3.isites.harvard.edu',
        'PORT': '8003',
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
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool.views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        }

    }
}
