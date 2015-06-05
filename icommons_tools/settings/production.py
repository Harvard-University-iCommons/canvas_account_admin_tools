from .base import *

import os

os.environ['http_proxy'] = 'http://10.34.5.254:8080'
os.environ['https_proxy'] = 'http://10.34.5.254:8080'

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
EXPORT_TOOL['ssh_private_key'] = '/home/icommons/.ssh/id_rsa'

TERM_TOOL = {
    'ADMIN_GROUP': 'IcGroup:25292',
    'ALLOWED_GROUPS': {
        'IcGroup:25096': 'gse',
        'IcGroup:25095': 'colgsas',
        'IcGroup:25097': 'hls',
        'IcGroup:25098': 'hsph',
        'IcGroup:25099': 'hds',
        'IcGroup:25100': 'gsd',
        'IcGroup:25101': 'ext',
        'IcGroup:25102': 'hks',
        'IcGroup:25103': 'hms',
        'IcGroup:25104': 'hsdm',
        'IcGroup:25105': 'hbsmba',
        'IcGroup:25106': 'hbsdoc',
        'IcGroup:25178': 'sum'
    },
    'ICOMMONS_EXT_TOOLS_BASE_URL': 'https://isites.harvard.edu',
}

CANVAS_WHITELIST['canvas_url'] = 'https://harvard.instructure.com/api'

GUNICORN_CONFIG = 'gunicorn_prod.py'

SENDFILE_BACKEND = 'sendfile.backends.xsendfile'
