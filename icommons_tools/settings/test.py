from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'SHOPPER_ROLE': 'Shopper',
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
    'ICOMMONS_EXT_TOOLS_BASE_URL': 'https://icommons-ext-tools.test.tlt.harvard.edu',
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
        'huey_logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/var/opt/tlt/logs/huey-icommons_tools.log',
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
        'huey': {
            'handlers': ['huey_logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# When starting gunicorn, this setting will tell the script which config to pull
GUNICORN_CONFIG = 'gunicorn_test.py'
