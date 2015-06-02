from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'icommons_tools.db.sqlite3',
    },
}

DATABASE_ROUTERS = []

EXPORT_TOOL['ssh_private_key'] = '/home/vagrant/.ssh/id_rsa'
