from .base import *
from logging.config import dictConfig

ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if not CANVAS_SHOPPING.get('selfreg_courses'):
    CANVAS_SHOPPING['selfreg_courses'] = {
        '5947': 'Guest',
    }

# NOTE: to run locally, you'll need to copy over your personal id_rsa token
# so vagrant can connect to the server.  Also, you'll need to copy over your
# .boto file in order to be able to download the exports
EXPORT_TOOL['ssh_private_key'] = '/home/vagrant/.ssh/id_rsa'

INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

# For Django Debug Toolbar:
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

dictConfig(LOGGING)
