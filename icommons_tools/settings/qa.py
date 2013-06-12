from .base import *

DEBUG = False

ALLOWED_HOSTS = ['termtool-qa.icommons.harvard.edu']

'''
Configure application settings

Also Required but not set here:
DJANGO_DB_PASSWORD - must be defined in the environment
CIPHER_KEY - must be defined in the environment

'''
APP_CONFIG = {
    'DJANGO_DB_HOST':'icd3.isites.harvard.edu',
    'DJANGO_DB_PORT':'8103',
    'DJANGO_DB_SID':'isitedev',
    'DJANGO_DB_USER':'coursemanager',
    'ICOMMONSAPIHOST':'https://isites.harvard.edu/services/',
    'ICOMMONSAPIUSER':'2CF64ADC-4907-11E1-B318-E3828F1150F0',
    'ICOMMONSAPIPASS':'z1KuYq7K2XFxtM4Fu91J',
    'TERM_TOOL_LOG':'term_tool.log'
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

'''
The dictionary below contains group id's and school names. 
These are the groups that are allowed to edit term informtion.
The school must be the same as the school_id in the school model.
'''
ADMIN_GROUP = 'IcGroup:18611'

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

