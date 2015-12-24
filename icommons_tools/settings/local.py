from .base import *
from logging.config import dictConfig

DEBUG = True

CRISPY_FAIL_SILENTLY = False

SECRET_KEY = 'changeme'

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

INSTALLED_APPS += ('debug_toolbar', 'sslserver')

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

# For Django Debug Toolbar:
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

dictConfig(LOGGING)

SELENIUM_CONFIG = {
    'project_base_url': 'https://icommons-tools.dev.tlt.harvard.edu/',
    'course_conclusion': {
        'cid': '339589',
        'course_data': [
            'Fall 2015',
            '339589',
            'Administration and Leadership',
            '2016-01-01'
        ],
        'index_page': 'course_conclusion/',
        'school': 'Divinity School'
    },
    'run_locally': False,
    'selenium_grid_url': SECURE_SETTINGS.get('selenium_grid_url'),
    'selenium_password': SECURE_SETTINGS.get('selenium_password'),
    'selenium_username': SECURE_SETTINGS.get('selenium_user'),
    'use_htmlrunner': SECURE_SETTINGS.get('selenium_use_htmlrunner', True),
    'term_tool_base_url': SECURE_SETTINGS.get('term_tool_base_url'),
    'term_tool_relative_url': SECURE_SETTINGS.get('term_tool_relative_url'),
    'canvas_base_url': SECURE_SETTINGS.get('canvas_url'),
    'course_shopping': {
        'user_HUID': SECURE_SETTINGS.get('shopping_user_HUID'),
        'user_password': SECURE_SETTINGS.get('shopping_user_password'),
        'relative_url': SECURE_SETTINGS.get('canvas_shopping_relative_url'),
    },

}
