from .local import *

DATABASE_APPS_MAPPING = {
    'auth': 'default',
    'canvas_account_admin_tools': 'default',
    'contenttypes': 'default',
    'course_info': 'default',
    'django_auth_lti': 'default',
    'icommons_common': 'default',
    'icommons_ui': 'default',
    'messages': 'default',
    'proxy': 'default',
    'sessions': 'default',
    'staticfiles': 'default',
}

DATABASE_MIGRATION_WHITELIST = ['default']

# Make tests faster by using sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'test.db'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    },
    'shared': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}
