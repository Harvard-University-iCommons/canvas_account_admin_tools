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
    dateTimeStamp = time.strftime('%Y%m%d_%H_%M_%S')
    buf = file("TestReport" + "_" + dateTimeStamp + ".html", 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
        stream=buf,
        title='icommons_tools selenium_tests',
        description='Result of Selenium tests in icommons_tools project'
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
result = runner.run(suite)
if not result.wasSuccessful():
    raise SystemExit(1)
