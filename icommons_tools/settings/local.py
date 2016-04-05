from .base import *
from logging.config import dictConfig

DEBUG = True

CRISPY_FAIL_SILENTLY = False

SECRET_KEY = '$9$s(^-=2p+u_9bl9k%to#(55ji8lx9k'

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

ICOMMONS_REST_API_TOKEN = SECURE_SETTINGS.get('icommons_rest_api_token')
ICOMMONS_REST_API_HOST = SECURE_SETTINGS.get('icommons_rest_api_host')

SELENIUM_CONFIG = {

    'canvas_base_url': SECURE_SETTINGS.get('canvas_url'),
    'debug': {
        'log_config': {
            'incremental': True,
            # prevents selenium debug messages when in local/text output mode
            'loggers': {'selenium': {'level': 'ERROR'}},
            'version': 1
        },
        # 'screenshots_on_failure': True,
    },
    'run_locally': SECURE_SETTINGS.get('selenium_run_locally', False),
    'selenium_grid_url': SECURE_SETTINGS.get('selenium_grid_url'),
    'selenium_password': SECURE_SETTINGS.get('selenium_password'),
    'selenium_username': SECURE_SETTINGS.get('selenium_user'),
    'use_htmlrunner': SECURE_SETTINGS.get('selenium_use_htmlrunner', True),

    'icommons_rest_api': {
        'base_path': 'api/course/v2'
    },

    'course_shopping': {
        'user_HUID': SECURE_SETTINGS['shopping_user_HUID'],
        'user_password': SECURE_SETTINGS['shopping_user_password'],
        'relative_url': 'courses/3762',
    },

    'term_tool_base_url': SECURE_SETTINGS['term_tool_base_url'],
    'exclude_courses_relative_url': 'term_tool/term/2601/colgsas/exclude_courses',

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
}
