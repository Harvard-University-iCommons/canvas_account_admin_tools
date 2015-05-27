from .base import *

DEBUG = False

ALLOWED_HOSTS = ['*']

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'selfreg_courses': {
        '495': 'Guest',
    },
    'SHOPPER_ROLE': 'Shopper',
    'ROOT_ACCOUNT': '1',
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
    'ICOMMONS_EXT_TOOLS_BASE_URL': 'https://icommons-ext-tools.qa.tlt.harvard.edu',
}

SESSION_COOKIE_SECURE = True

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
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': True,
        },
        'term_tool': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'canvas_shopping': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'isites_export_tool': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'qualtrics_whitelist': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'qualtrics_taker_auth': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'icommons_common': {
            'handlers': ['logfile'],
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


GUNICORN_CONFIG = 'gunicorn_qa.py'
