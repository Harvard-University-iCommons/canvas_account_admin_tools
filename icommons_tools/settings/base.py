# Django settings for icommons_tools project.
import os
from .secure import SECURE_SETTINGS
from django.core.urlresolvers import reverse_lazy
import logging
import time

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Make this unique, and don't share it with anybody.
SECRET_KEY = SECURE_SETTINGS.get('django_secret_key', 'changeme')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SECURE_SETTINGS.get('enable_debug', False)

TEMPLATE_DEBUG = DEBUG

# This is the address that emails will be sent "from"
# See other specific email settings in AWS or local.py files
SERVER_EMAIL = 'iCommons Tools <icommons-bounces@harvard.edu>'

# DATABASES are defined in individual environment settings

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

# STATIC_ROOT can be overriden in individual environment settings
STATIC_ROOT = os.path.normpath(os.path.join(BASE_DIR, 'http_static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.normpath(os.path.join(BASE_DIR, 'static')),
)


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cached_auth.Middleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'icommons_common.auth.backends.PINAuthBackend',
)

CAS_LOGOUT_URL = 'http://login.icommons.harvard.edu/pinproxy/logout'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "icommons_common.auth.context_processors.pin_context",
)

ROOT_URLCONF = 'icommons_tools.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'icommons_tools.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.webdesign',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'icommons_common',
    'icommons_common.monitor',
    'icommons_ui',
    'term_tool',
    'qualtrics_taker_auth',
    'canvas_shopping',
    'qualtrics_whitelist',
    'canvas_whitelist',
    # 'gunicorn',
    'crispy_forms',
    'isites_export_tool',
    'huey.djhuey',
    'rest_framework',
    'course_conclusion',
)

# session cookie lasts for 7 hours (in seconds)
SESSION_COOKIE_AGE = 60 * 60 * 7

SESSION_COOKIE_NAME = 'djsessionid'

SESSION_COOKIE_HTTPONLY = True

CRISPY_TEMPLATE_PACK = 'bootstrap3'

CRISPY_FAIL_SILENTLY = not DEBUG

LOGIN_URL = reverse_lazy('pin:login')

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_APPS_MAPPING = {
    'auth': 'default',
    'contenttypes': 'default',
    'sessions': 'default',
    'canvas_shopping': 'default',
    'canvas_whitelist': 'default',
    'icommons_common': 'termtool',
    'icommons_ui': 'default',
    'isites_export_tool': 'termtool',
    'qualtrics_whitelist': 'default',
    'term_tool': 'default',
}

DATABASE_MIGRATION_WHITELIST = ['default']

DATABASE_ROUTERS = ['icommons_common.routers.DatabaseAppsRouter', ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': SECURE_SETTINGS.get('db_default_name', 'icommons_tools'),
        'USER': SECURE_SETTINGS.get('db_default_user', 'postgres'),
        'PASSWORD': SECURE_SETTINGS.get('db_default_password'),
        'HOST': SECURE_SETTINGS.get('db_default_host', '127.0.0.1'),
        'PORT': SECURE_SETTINGS.get('db_default_port', 5432),  # Default postgres port
    },
    'termtool': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': SECURE_SETTINGS.get('django_db'),
        'USER': SECURE_SETTINGS.get('django_db_user'),
        'PASSWORD': SECURE_SETTINGS.get('django_db_pass'),
        'HOST': SECURE_SETTINGS.get('django_db_host'),
        'PORT': str(SECURE_SETTINGS.get('django_db_port')),
        'OPTIONS': {
            'threaded': True,
        },
        'CONN_MAX_AGE': 0,
    }
}

# CACHE

REDIS_HOST = SECURE_SETTINGS.get('redis_host', '127.0.0.1')
REDIS_PORT = SECURE_SETTINGS.get('redis_port', 6379)

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': "%s:%s" % (REDIS_HOST, REDIS_PORT),
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
        'TIMEOUT': SESSION_COOKIE_AGE,  # Tie default timeout to session cookie age
        # Provide a unique value for sharing cache among Django projects
        'KEY_PREFIX': 'icommons_tools',
    },
}

# SESSIONS (store in cache)

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Django defaults to False (as of 1.7)
# SESSION_COOKIE_SECURE = SECURE_SETTINGS.get('use_secure_cookies', False)

"""
Tool specific settings below
"""

# Base url for canvas, default to harvard iCommons instance
CANVAS_URL = SECURE_SETTINGS.get('canvas_url', 'https://canvas.icommons.harvard.edu')

HUEY = {
    'backend': 'huey.backends.redis_backend',
    'connection': {'host': REDIS_HOST, 'port': int(REDIS_PORT)},  # huey needs redis port to be an int
    'always_eager': False,  # Defaults to False when running via manage.py run_huey
    'consumer_options': {'workers': 4},  # probably needs tweaking
    'name': 'huey-icommons-tools-queue',
}

# Used by django_icommons_common library
ICOMMONS_COMMON = {
    # Default to qa
    'ICOMMONS_API_HOST': SECURE_SETTINGS.get('icommons_api_host', 'https://10.35.201.5/services/'),
    'ICOMMONS_API_USER': SECURE_SETTINGS.get('icommons_api_user', None),
    'ICOMMONS_API_PASS': SECURE_SETTINGS.get('icommons_api_pass', None),
    'CANVAS_API_BASE_URL': CANVAS_URL + '/api/v1',  # Can be overriden in environment settings file
    'CANVAS_API_HEADERS': {'Authorization': 'Bearer ' + SECURE_SETTINGS.get('canvas_token', 'canvas_token_missing_from_config')},
}

CANVAS_SDK_SETTINGS = {
    'auth_token': SECURE_SETTINGS.get('canvas_token', 'canvas_token_missing_from_config'),
    'base_api_url': CANVAS_URL + '/api',
    'max_retries': 3,
    'per_page': 1000,
}

QUALTRICS_TAKER_AUTH = {
    'QUALTRICS_API_KEY': SECURE_SETTINGS.get('qualtrics_api_key', None),
    'BITLY_ACCESS_TOKEN': SECURE_SETTINGS.get('bitly_access_token', None),
}

QUALTRICS_WHITELIST = {
    'allowed_groups': 'IcGroup:358',
}

CANVAS_WHITELIST = {
    'allowed_groups': 'IcGroup:358',
    'canvas_url': CANVAS_URL + '/api',
    'oauth_token': SECURE_SETTINGS.get('canvas_token', 'canvas_token_missing_from_config'),
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
        'IcGroup:25178': 'sum',
        'IcGroup:32222': 'ksg'
    },
}

CANVAS_SHOPPING = {
    'SHOPPER_ROLE': 'Shopper',
    'ROOT_ACCOUNT': '1',
}

COURSE_CONCLUDE_TOOL = {
    'years_back': 5,
}

# Default secure/env settings to production
EXPORT_TOOL = {
    'ssh_user': 'icommons',
    'ssh_hostname': SECURE_SETTINGS.get('isites_export_ssh_hostname', 'tool2.isites.harvard.edu'),
    'ssh_private_key': '/home/deploy/.ssh/id_rsa',  # AWS user, so override for non-AWS envs
    'create_site_zip_cmd': 'perl /u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_s3.pl',
    'archive_cutoff_time_in_hours': SECURE_SETTINGS.get('isites_export_archive_cutoff_time_in_hours', 48),
    'archive_task_crontab_hours': "*/1",  # hourly frequency that periodic task executes in crontab format
    'allowed_groups': ['IcGroup:358', 'IcGroup:29819'],
    's3_bucket': SECURE_SETTINGS.get('isites_export_s3_bucket', ''),
    's3_download_url_expiration_in_secs': SECURE_SETTINGS.get('isites_export_s3_download_url_expiration_in_secs', 60),
}

_DEFAULT_LOG_LEVEL = SECURE_SETTINGS.get('log_level', logging.DEBUG)
_LOG_ROOT = SECURE_SETTINGS.get('log_root', '')  # Default to current directory

# Make sure log timestamps are in GMT
logging.Formatter.converter = time.gmtime

# Turn off default Django logging
# https://docs.djangoproject.com/en/1.8/topics/logging/#disabling-logging-configuration
LOGGING_CONFIG = None

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s\t%(asctime)s.%(msecs)03dZ\t%(name)s:%(lineno)s\t%(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s\t%(name)s:%(lineno)s\t%(message)s',
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        # Log to a text file that can be rotated by logrotate
        'app_logfile': {
            'level': _DEFAULT_LOG_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.normpath(os.path.join(_LOG_ROOT, 'django-icommons_tools.log')),
            'formatter': 'verbose',
        },
        'huey_logfile': {
            'level': _DEFAULT_LOG_LEVEL,
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.normpath(os.path.join(_LOG_ROOT, 'huey-icommons_tools.log')),
            'formatter': 'verbose',
        },
        'console': {
            'level': _DEFAULT_LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
        },
    },
    # This is the default logger for any apps or libraries that use the logger
    # package, but are not represented in the `loggers` dict below.  A level
    # must be set and handlers defined.  Setting this logger is equivalent to
    # setting and empty string logger in the loggers dict below, but the separation
    # here is a bit more explicit.  See link for more details:
    # https://docs.python.org/2.7/library/logging.config.html#dictionary-schema-details
    'root': {
        'level': logging.WARNING,
        'handlers': ['console', 'app_logfile'],
    },
    'loggers': {
        'canvas_whitelist': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'term_tool': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'canvas_shopping': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'course_conclusion': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'isites_export_tool': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'qualtrics_whitelist': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'qualtrics_taker_auth': {
            'handlers': ['console', 'app_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'huey': {
            'handlers': ['console', 'huey_logfile'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },

    }
}
