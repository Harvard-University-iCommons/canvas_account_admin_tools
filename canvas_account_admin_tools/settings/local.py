from .base import *
from logging.config import dictConfig

ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += ('debug_toolbar', 'sslserver')
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

# For Django Debug Toolbar:
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

dictConfig(LOGGING)

# Allows the REST API passthrough to successfully negotiate an SSL session
# with an unverified certificate, e.g. the one that ships with django-sslserver
ICOMMONS_REST_API_SKIP_CERT_VERIFICATION = True

SELENIUM_CONFIG = {
   'account_admin': {
      'relative_url': 'accounts/1/external_tools/20',
   },
   'canvas_base_url': CANVAS_URL,
   'course_info_tool': {
      'relative_url': 'accounts/1/external_tools/20',
      'test_course': {
         'cid': '339331',
         'term': 'Spring',
         'title': 'Latin Paleography and Manuscript Culture: Seminar',
         'school': 'Divinity School',
         'type': 'Only courses without sites',
         'year': '2014',
      },
      'test_users': {
         'existing': {
            'user_id': '20299916'
         },
         'new': {
            'role': 'Teacher',
            'user_id': '30833767'
         }
      }
   },
   'run_locally': False,
   'selenium_username': SECURE_SETTINGS.get('selenium_user'),
   'selenium_password': SECURE_SETTINGS.get('selenium_password'),
   'selenium_grid_url': SECURE_SETTINGS.get('selenium_grid_url'),
   'use_htmlrunner': SECURE_SETTINGS.get('selenium_use_htmlrunner', True),

}
