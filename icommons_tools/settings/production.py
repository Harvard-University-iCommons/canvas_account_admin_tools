from .base import *

import os

os.environ['http_proxy'] = 'http://10.34.5.254:8080'
os.environ['https_proxy'] = 'http://10.34.5.254:8080'

# debug must be false for production
DEBUG = False

# to prevent host header poisoning
ALLOWED_HOSTS = ['*']

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'selfreg_courses': {
        '495': 'Guest',
        '541': 'Guest',
        '471': 'StudentEnrollment',
        '879': 'StudentEnrollment',
        '906': 'StudentEnrollment',
        '913': 'Shopper',
        '935': 'StudentEnrollment',
        '741': 'Shopper',
        '743': 'Shopper',
        '774': 'Shopper',
        '1858': 'StudentEnrollment',
        '1972': 'StudentEnrollment',
        '1973': 'StudentEnrollment',
        '2049': 'StudentEnrollment',
        '2290': 'StudentEnrollment',
        '2311': 'StudentEnrollment',
        '2325': 'Shopper',
        '2490': 'Shopper',
        '2816': 'StudentEnrollment',
        '2821': 'StudentEnrollment',
        '2874': 'StudentEnrollment',
        '2878': 'StudentEnrollment'
    },
    'SHOPPER_ROLE': 'Shopper',
    'VIEWER_ROLE': 'Harvard-Viewer',
    'ROOT_ACCOUNT': '1',
}

EXPORT_TOOL = {
    'base_file_download_url': 'http://poll.icommons.harvard.edu/exports/',
    'ssh_hostname': 'icommons@tool2.isites.harvard.edu',  # name used to connect via ssh to perl script server
    'ssh_private_key': '/home/icommons/.ssh/id_rsa',
    'create_site_zip_cmd': 'ORACLE_HOME=/u01/app/oracle/product/11.1.0 LD_LIBRARY_PATH=/u01/app/oracle/product/11.1.0/lib32 /u02/icommons/perl-5.12.0/bin/perl /u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl',
    'remove_site_zip_cmd': 'ORACLE_HOME=/u01/app/oracle/product/11.1.0 LD_LIBRARY_PATH=/u01/app/oracle/product/11.1.0/lib32 /u02/icommons/perl-5.12.0/bin/perl /u02/icommons/perlapps/iSitesAPI/scripts/rm_export_file.pl',
    'archive_cutoff_time_in_hours': 24 * 7,  # express cutoff time in hours
    'archive_task_crontab_hours': "*/1",  # hourly frequency that periodic task executes in crontab format
    'allowed_groups': ['IcGroup:358','IcGroup:29819'],
    'local_archive_dir': '/appdata/icommons_tools/isites_export',
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
}

CANVAS_WHITELIST['canvas_url'] = 'https://harvard.instructure.com/api'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'isitedgd',
        'USER': SECURE_SETTINGS.get('django_db_user', None),
        'PASSWORD': SECURE_SETTINGS.get('django_db_pass', None),
        'HOST': 'dbnode3.isites.harvard.edu',
        'PORT': '8003',
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
            'filename': '/logs/icommons_tools/icommons_tools.log',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'huey_logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/logs/icommons_tools/huey.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'canvas_shopping': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'DEBUG',
            'propagate': True,
        },
        'qualtrics_taker_auth': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'qualtrics_whitelist': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'isites_export_tool': {
            'handlers': ['mail_admins', 'logfile', ],
            'level': 'INFO',
            'propagate': True,
        },
        'huey': {
            'handlers': ['mail_admins', 'huey_logfile', ],
            'level': 'ERROR',
            'propagate': True,
        },

    }
}


SESSION_COOKIE_SECURE = True

GUNICORN_CONFIG = 'gunicorn_prod.py'

SENDFILE_BACKEND = 'sendfile.backends.xsendfile'
