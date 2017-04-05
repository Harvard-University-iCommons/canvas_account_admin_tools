from .base import *

DEBUG = True

SECRET_KEY = 'zd_*c@fm5@inktc5jo1y+t=6m&fx0$81f=vjv*^nk894cfgyg@'

ENV_NAME = 'test'

# no router necessary in a test environment
DATABASE_ROUTERS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': SECURE_SETTINGS.get('db_default_name', 'canvas_account_admin_tools_test'),
        'USER': SECURE_SETTINGS.get('db_default_user', 'postgres'),
        'PASSWORD': SECURE_SETTINGS.get('db_default_password'),
        'HOST': SECURE_SETTINGS.get('db_default_host', '127.0.0.1'),
        'PORT': SECURE_SETTINGS.get('db_default_port', 5432),  # Default postgres port
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'shared': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}

RQWORKER_QUEUE_NAME = 'test'
RQ_QUEUES[RQWORKER_QUEUE_NAME] = RQ_QUEUES['default']

# Set logging back to the default
LOGGING_CONFIG = 'logging.config.dictConfig'
