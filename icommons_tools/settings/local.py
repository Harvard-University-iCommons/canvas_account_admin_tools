from .base import *

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'selfreg_courses': {
        '5947': 'Guest',
    },
    'SHOPPER_ROLE': 'Shopper',
    'ROOT_ACCOUNT': '1',
}

# NOTE: to run locally, you'll need to copy over your personal id_rsa token
# so vagrant can connect to the server.  Also, you'll need to copy over your
# .boto file in order to be able to download the exports
EXPORT_TOOL['ssh_private_key'] = '/home/vagrant/.ssh/id_rsa'

TERM_TOOL['ICOMMONS_EXT_TOOLS_BASE_URL'] = 'http://localhost:8000'

INSTALLED_APPS += (
    'debug_toolbar',
    'rest_framework.authtoken',
)

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

# For Django Debug Toolbar:
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

'''
The dictionary below contains group id's and school names.
These are the groups that are allowed to edit term informtion.
The school must be the same as the school_id in the school model.
'''


GUNICORN_CONFIG = 'gunicorn_local.py'
