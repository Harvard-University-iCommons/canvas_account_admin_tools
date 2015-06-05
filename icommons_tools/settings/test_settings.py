from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'icommons_tools.db.sqlite3',
    },
}

DATABASE_ROUTERS = []
