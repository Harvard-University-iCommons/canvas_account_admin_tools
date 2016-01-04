import os
import sys
import time
import unittest

from django.conf import settings

# set up PYTHONPATH and DJANGO_SETTINGS_MODULE.  icky, but necessary
pwd = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(pwd, '..')))
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.putenv('DJANGO_SETTINGS_MODULE', 'icommons_tools.settings.local')

# developing test cases is easier with text test runner, lets us drop into pdb
if settings.SELENIUM_CONFIG.get('use_htmlrunner', True):
    from selenium_common import HTMLTestRunner

    # This relative path should point to BASE_DIR/selenium_tests/reports
    report_file_path = os.path.relpath('./reports')
    if not os.path.exists(report_file_path):
        os.makedirs(report_file_path)

    dateTimeStamp = time.strftime('%Y%m%d_%H_%M_%S')
    report_name = "canvas_account_admin_tools_test_report_{}.html".format(
        dateTimeStamp)
    report_file_obj = file(os.path.join(report_file_path, report_name), 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
        stream=report_file_obj,
        title='Canvas Account Admint Tools test suite report',
        description='Result of tests in {}'.format(__file__)
    )
else:
    import logging; logging.basicConfig(level=logging.DEBUG)
    runner = unittest.TextTestRunner()

# load in all unittest.TestCase objects from *_tests.py files.  start in PWD,
# with top_level_dir set to PWD/..
suite = unittest.defaultTestLoader.discover(
    os.path.abspath(pwd),
    pattern='*_tests.py',
    top_level_dir=os.path.abspath(os.path.join(pwd, '..'))
)

# run the suite
runner.run(suite)
