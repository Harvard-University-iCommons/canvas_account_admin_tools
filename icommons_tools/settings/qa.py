from .base import *

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'selfreg_courses': {
        '495': 'Guest',
    },
    'SHOPPER_ROLE': 'Shopper',
    'ROOT_ACCOUNT': '1',
}

TERM_TOOL['ICOMMONS_EXT_TOOLS_BASE_URL'] = 'https://icommons-ext-tools.qa.tlt.harvard.edu'

GUNICORN_CONFIG = 'gunicorn_qa.py'
