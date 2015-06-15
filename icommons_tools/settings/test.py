from .base import *

CANVAS_SHOPPING = {
    'CANVAS_BASE_URL': CANVAS_URL,
    'SHOPPER_ROLE': 'Shopper',
}

TERM_TOOL['ICOMMONS_EXT_TOOLS_BASE_URL'] = 'https://icommons-ext-tools.test.tlt.harvard.edu'

# When starting gunicorn, this setting will tell the script which config to pull
GUNICORN_CONFIG = 'gunicorn_test.py'
