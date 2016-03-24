from .base import *
from logging.config import dictConfig

ALLOWED_HOSTS = ['*']

DEBUG = True  # Always run in debug mode locally

#  Dummy secret key value for testing and local usage
SECRET_KEY = "q9frwftd7&)vn9zonjy2&vgmq1i9csn20+f0r5whb%%u-mzm_i"

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
      'relative_url': 'accounts/10/external_tools/79',  # dev (Admin Console)
   },
   'canvas_base_url': CANVAS_URL,
   'course_info_tool': {
      # 'relative_url': 'accounts/8/external_tools/9',  # local
      'relative_url': 'accounts/10/external_tools/79',  # dev (Admin Console)
      'test_course': {
         'cid': '339331',
         'term': 'Spring',
         'title': 'Latin Paleography and Manuscript Culture: Seminar',
         'registrar_code_display': '2223',
         'school': 'Divinity School',
         'type': 'Only courses without sites',
         'year': '2014',
      },
      'test_course_with_registrar_code_display_not_populated_in_db': {
         'cid': '353457',
         'registrar_code': 'selenium_test',
         'school': 'Harvard College/GSAS',
      },
      'test_users': {
         'existing': {
            'role_id': '9',
            'user_id': '20299916'
         },
      }
   },
   'icommons_rest_api': {
      'base_path': 'api/course/v2'
   },
   'run_locally': False,
   'selenium_username': SECURE_SETTINGS.get('selenium_user'),
   'selenium_password': SECURE_SETTINGS.get('selenium_password'),
   'selenium_grid_url': SECURE_SETTINGS.get('selenium_grid_url'),
   'use_htmlrunner': SECURE_SETTINGS.get('selenium_use_htmlrunner', True),
}

CONCLUDE_COURSES_URL = SECURE_SETTINGS.get(
    'conclude_courses_url',
    'https://icommons-tools.dev.tlt.harvard.edu/course_conclusion'
)
