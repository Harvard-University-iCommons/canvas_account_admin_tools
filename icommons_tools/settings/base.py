# Django settings for icommons_tools project.
from .secure import SECURE_SETTINGS

from os.path import abspath, basename, dirname, join, normpath
from sys import path
from django.core.urlresolvers import reverse_lazy


### Path stuff as recommended by Two Scoops / with local mods

# Absolute filesystem path to the Django project config directory:
# (this is the parent of the directory where this file resides,
# since this file is now inside a 'settings' pacakge directory)
DJANGO_PROJECT_CONFIG = dirname(dirname(abspath(__file__)))

# Absolute filesystem path to the top-level project folder:
# (this is one directory up from the project config directory)
SITE_ROOT = dirname(DJANGO_PROJECT_CONFIG)

# Site name:
SITE_NAME = basename(SITE_ROOT)

# Add our project to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(SITE_ROOT)

### End path stuff

# THESE ADDRESSES WILL RECEIVE EMAIL ABOUT CERTAIN ERRORS!
# NOTE: this was being set to a sample email address in non-prod
# environments before this change.  This represents the address used
# for prod.
ADMINS = (
    ('iCommons Tech', 'icommons-technical@g.harvard.edu'),
),

# This is the address that emails will be sent "from"
SERVER_EMAIL = 'iCommons Tools <icommons-bounces@harvard.edu>'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mailhost.harvard.edu'
EMAIL_USE_TLS = True

MANAGERS = ADMINS

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
STATIC_ROOT = normpath(join(SITE_ROOT, 'http_static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/tools/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #normpath(join(SITE_ROOT, 'static')),
)


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = SECURE_SETTINGS.get('django_secret_key', 'changeme')

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
    'djsupervisor',
)

# session cookie lasts for 7 hours (in seconds)
SESSION_COOKIE_AGE = 60 * 60 * 7

SESSION_COOKIE_NAME = 'djsessionid'

SESSION_COOKIE_HTTPONLY = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CRISPY_TEMPLATE_PACK = 'bootstrap3'

LOGIN_URL = reverse_lazy('pin:login')

# Base url for canvas, default to harvard iCommons instance
CANVAS_URL = SECURE_SETTINGS.get('canvas_url', 'https://canvas.icommons.harvard.edu')

"""
database settings
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': SECURE_SETTINGS.get('django_db_name', None),
        'USER': SECURE_SETTINGS.get('django_db_user', None),
        'PASSWORD': SECURE_SETTINGS.get('django_db_pass', None),
        'HOST': SECURE_SETTINGS.get('django_db_host', None),
        'PORT': SECURE_SETTINGS.get('django_db_port', None),
        'OPTIONS': {
            'threaded': True,
        },
        'CONN_MAX_AGE': 1200,
    }
}

"""
Tool specific settinsg below
"""

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
    'oauth_token': SECURE_SETTINGS.get('canvas_whitelist_oauth_token', None),
}

