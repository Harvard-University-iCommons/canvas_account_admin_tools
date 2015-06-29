from .base import *

import os

# debug must be false for production
DEBUG = False

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'selfreg_courses': {
        '495': 'Guest',
        '541': 'Guest',
        '471': 'StudentEnrollment',
        '879': 'StudentEnrollment',
        '906': 'StudentEnrollment',
        '913': 'Shopper',
        '935': 'StudentEnrollment',
        '741': 'Shopper',
        '743': 'Shopper',
        '774': 'Shopper',
        '1858': 'StudentEnrollment',
        '1972': 'StudentEnrollment',
        '1973': 'StudentEnrollment',
        '2049': 'StudentEnrollment',
        '2290': 'StudentEnrollment',
        '2311': 'StudentEnrollment',
        '2325': 'Shopper',
        '2490': 'Shopper',
        '2816': 'StudentEnrollment',
        '2821': 'StudentEnrollment',
        '2874': 'StudentEnrollment',
        '2878': 'StudentEnrollment'
    },
    'SHOPPER_ROLE': 'Shopper',
    'ROOT_ACCOUNT': '1',
}

# NOTE: ORACLE environment variables have already been established for
# ssh user in production, so the create and remove commands can be called
# in the same way across all environments.

TERM_TOOL['ICOMMONS_EXT_TOOLS_BASE_URL'] = 'https://isites.harvard.edu'

CANVAS_WHITELIST['canvas_url'] = 'https://harvard.instructure.com/api'

GUNICORN_CONFIG = 'gunicorn_prod.py'

SENDFILE_BACKEND = 'sendfile.backends.xsendfile'
