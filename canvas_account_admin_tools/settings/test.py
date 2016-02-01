from .local import *

# so that the CourseSchemaDatabaseRouter doesn't look for a non-existent
# termtool database connection
DATABASE_ROUTERS = []

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
