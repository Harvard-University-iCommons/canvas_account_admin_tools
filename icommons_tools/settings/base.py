# Django settings for icommons_tools project.
import os
from .secure import SECURE_SETTINGS
from django.core.urlresolvers import reverse_lazy
import logging
import time

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# This is the address that emails will be sent "from"
# See other specific email settings in AWS or local.py files
SERVER_EMAIL = 'iCommons Tools <icommons-bounces@harvard.edu>'


# Application definition
INSTALLED_APPS = [
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'icommons_common',
    'icommons_common.monitor',
    'icommons_ui',
    'term_tool',
    'qualtrics_taker_auth',
    'canvas_shopping',
    'qualtrics_whitelist',
    'canvas_whitelist',
    'crispy_forms',
    'isites_export_tool',
    'huey.djhuey',
    'course_conclusion',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cached_auth.Middleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'icommons_tools.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'icommons_common.auth.context_processors.pin_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'icommons_tools.wsgi.application'

# Database
# https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/#databases

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASE_ROUTERS = ['icommons_common.routers.CourseSchemaDatabaseRouter']

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

COURSE_SCHEMA_DB_NAME = 'termtool'

# Cache
# https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-CACHES

REDIS_HOST = SECURE_SETTINGS.get('redis_host', '127.0.0.1')
REDIS_PORT = SECURE_SETTINGS.get('redis_port', 6379)

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': "redis://%s:%s/0" % (REDIS_HOST, REDIS_PORT),
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
        'KEY_PREFIX': 'icommons_tools',  # Provide a unique value for shared cache
        # See following for default timeout (5 minutes as of 1.7):
        # https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-CACHES-TIMEOUT
        'TIMEOUT': SECURE_SETTINGS.get('default_cache_timeout_secs', 300),
    },
}

# Sessions
# https://docs.djangoproject.com/en/1.8/topics/http/sessions/#module-django.contrib.sessions

# Store sessions in default cache defined below
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

SESSION_COOKIE_AGE = 60 * 60 * 7  # session cookie lasts for 7 hours (in seconds)

SESSION_COOKIE_NAME = 'djsessionid'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.normpath(os.path.join(BASE_DIR, 'http_static'))

STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.normpath(os.path.join(BASE_DIR, 'static')),
]

# Authentication Backends
# https://docs.djangoproject.com/en/1.8/topics/auth/customizing/#authentication-backends

AUTHENTICATION_BACKENDS = (
    'icommons_common.auth.backends.PINAuthBackend',
)

CAS_LOGOUT_URL = 'http://login.icommons.harvard.edu/pinproxy/logout'

LOGIN_URL = reverse_lazy('pin:login')

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Logging
# https://docs.djangoproject.com/en/1.8/topics/logging/#configuring-logging

# Make sure log timestamps are in GMT
logging.Formatter.converter = time.gmtime

# Turn off default Django logging
# https://docs.djangoproject.com/en/1.8/topics/logging/#disabling-logging-configuration
LOGGING_CONFIG = None

_DEFAULT_LOG_LEVEL = SECURE_SETTINGS.get('log_level', logging.DEBUG)
_LOG_ROOT = SECURE_SETTINGS.get('log_root', '')

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
    'handlers': {
        # By default, log to a file
        'default': {
            'class': 'logging.handlers.WatchedFileHandler',
            'level': _DEFAULT_LOG_LEVEL,
            'formatter': 'verbose',
            'filename': os.path.join(_LOG_ROOT, 'django-icommons_tools.log'),
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
        'handlers': ['default'],
    },
    'loggers': {
        'canvas_whitelist': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'term_tool': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'canvas_shopping': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'course_conclusion': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'isites_export_tool': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'qualtrics_whitelist': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'qualtrics_taker_auth': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
        'huey': {
            'handlers': ['default'],
            'level': _DEFAULT_LOG_LEVEL,
            'propagate': False,
        },
    }
}


"""
Tool specific settings below
"""

# Base url for canvas, default to harvard iCommons instance
CANVAS_URL = SECURE_SETTINGS.get('canvas_url', 'https://canvas.dev.tlt.harvard.edu')

HUEY = {
    'backend': 'huey.backends.redis_backend',
    'connection': {'host': REDIS_HOST, 'port': int(REDIS_PORT)},  # huey needs redis port to be an int
    'always_eager': False,  # Defaults to False when running via manage.py run_huey
    # Have periodic task scheduler wake up every hour by default instead of every minute
    'consumer_options': {
        'workers': SECURE_SETTINGS.get('isites_export_huey_worker_threads', 2),
        'periodic_task_interval': SECURE_SETTINGS.get('isites_export_huey_periodic_task_interval_secs', 60 * 60),
    },
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
        'IcGroup:32222': 'ksg',
        'IcGroup:32569': 'mit',
    },
}

CANVAS_SHOPPING = {
    'SHOPPER_ROLE': 'Shopper',
    'ROOT_ACCOUNT': '1',
}

EXCLUDE_COURSES = {
    'allowed_group': 'IcGroup:358',
}

COURSE_CONCLUDE_TOOL = {
    'allowed_groups': {
        'IcGroup:193': ['hds'],
        'IcGroup:196': ['hls'],
        'IcGroup:218': ['gse'],
        'IcGroup:299': ['ext', 'sum'],
        'IcGroup:311': ['gsd'],
        'IcGroup:32471': ['hks'],
        'IcGroup:400': ['hsph'],
        'IcGroup:5257': ['ksg'],
        'IcGroup:533': ['colgsas'],
        'IcGroup:7528': ['hilr'],
    },
    'years_back': 5,
}

# Default secure/env settings to production
EXPORT_TOOL = {
    'ssh_user': 'icommons',
    'ssh_hostname': SECURE_SETTINGS.get('isites_export_ssh_hostname', 'tool2.isites.harvard.edu'),
    'ssh_private_key': '/home/deploy/.ssh/id_rsa',  # AWS user, so override for non-AWS envs
    'create_site_zip_cmd': 'perl /u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_s3.pl',
    'archive_cutoff_time_in_hours': SECURE_SETTINGS.get('isites_export_archive_cutoff_time_in_hours', 48),
    # Default to running at the start of every hour
    'archive_task_crontab': {
        'minute': SECURE_SETTINGS.get('isites_export_archive_task_crontab_minute', '0'),
        'hour': SECURE_SETTINGS.get('isites_export_archive_task_crontab_hour', '*'),
    },
    'allowed_groups': ['IcGroup:358', 'IcGroup:29819'],
    's3_bucket': SECURE_SETTINGS.get('isites_export_s3_bucket', ''),
    's3_download_url_expiration_in_secs': SECURE_SETTINGS.get('isites_export_s3_download_url_expiration_in_secs', 60),
}
