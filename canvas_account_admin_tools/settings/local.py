import sys
import oracledb
oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb
import cx_Oracle

import urllib3
urllib3.disable_warnings()

from .base import *
from logging.config import dictConfig

DEBUG = True  # Always run in debug mode locally

#  Dummy secret key value for testing and local usage
SECRET_KEY = "q9frwftd7&)vn9zonjy2&vgmq1i9csn20+f0r5whb%%u-mzm_i"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CANVAS_EMAIL_NOTIFICATION['course_migration_success_subject'] += ' (TEST, PLEASE IGNORE)'
CANVAS_EMAIL_NOTIFICATION['course_migration_failure_subject'] += ' (TEST, PLEASE IGNORE)'
CANVAS_EMAIL_NOTIFICATION['support_email_subject_on_failure'] += ' (TEST, PLEASE IGNORE)'
CANVAS_EMAIL_NOTIFICATION['support_email_address'] = 'tltqaemails@g.harvard.edu'

ALLOWED_HOSTS = ['*']
INSTALLED_APPS += ['django_extensions']

# If you want to use the Django Debug Toolbar, uncomment the following block:
'''
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
'''

# Allows the REST API passthrough to successfully negotiate an SSL session
# with an unverified certificate, e.g. the one that ships with django-sslserver
ICOMMONS_REST_API_SKIP_CERT_VERIFICATION = True

SELENIUM_CONFIG = {
   'account_admin': {
      'relative_url': 'accounts/10/external_tools/79',  # dev (Admin Console)
      #'relative_url': 'accounts/10/external_tools/99',  # qa (Admin Console)
   },
    'canvas_site_creator': {
        'test_data': {
            'course_code': 'Selenium-Automated',  # defaults to ILE
            'course_group': 'Anthropology',
            'course_short_title': 'Selenium Auto Test 101',
            'course_title': 'Selenium Automated Test Course 101',
            'template': 'None',  # No Template
            # Term used to be by value, but since the tool is displaying
            # two different dropdown element values
            # (see: https://github.com/Harvard-University-iCommons/
            # canvas_account_admin_tools/pull/176#discussion_r90055379)
            # the term value is modified to look by term display text.
            'term': 'Fall 2016',

            #TLT-2522 - Testing course with and without registrar_code_display
            'course_with_registrar_code_display': {
                'registrar_code_display': 'Automated_Test',
                'sis_id_value': '362568',
            },
            'course_without_registrar_code_display': {
                'registrar_code_display': '117138',
                'sis_id_value': '360031',
            },
        },
    },
   'canvas_base_url': CANVAS_URL,
   'course_info_tool': {
      # 'relative_url': 'accounts/8/external_tools/68',  # local
      'relative_url': 'accounts/10/external_tools/79',  # dev (Admin Console)
      'test_course': {
         'cid': '353035',
         'term': 'Spring',
         'title': 'Caribbean Poetics',
         'registrar_code_display': 'HDS 2430',
         'school': 'Harvard Divinity School',
         'type': 'All courses',
         'year': '2016',
      },
      'test_course_with_registrar_code_display_not_populated_in_db': {
         'cid': '353457',
         'registrar_code': 'selenium_test',
         'school': 'Harvard College/GSAS',
      },
      # only SB/ILE courses support editing through the course info tool at the
      # moment, so use this course for testing edit functionality
      'test_course_SB_ILE': {
         'cid': '354962',  # Canvas course 3591
         'term': 'Spring',
         'title': 'HDS Spring 2016',
         'school': 'Harvard Divinity School',
         'type': 'All courses',
         'year': '2016',
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

    'publish_courses': {
        'test_course': {
            'relative_url': 'courses/2601'
        },
        'test_terms': {
            'with_unpublished_courses': 'Summer 2017',
            'with_all_published_courses': 'Full Year 2016',
        },
        # When testing on a term with large number of courses, test in dry
        # run mode first to verify that numbers match expected results.
        'op_config': {
            'account': 10,
            #'courses': [],
            #'dry_run': False
            'term': "sis_term_id:2016-0",
            'published': 'false',
            },
     },

   'run_locally': SECURE_SETTINGS.get('selenium_run_locally', False),
   'selenium_username': SECURE_SETTINGS.get('selenium_user'),
   'selenium_password': SECURE_SETTINGS.get('selenium_password'),
   'selenium_grid_url': SECURE_SETTINGS.get('selenium_grid_url'),
   'use_htmlrunner': SECURE_SETTINGS.get('selenium_use_htmlrunner', True),
}

dictConfig(LOGGING)
