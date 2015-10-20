"""
To run these tests from the command line in a local VM, you'll need to set up the environment:
> export PYTHONPATH=/home/vagrant/canvas_account_admin_tools
> export DJANGO_SETTINGS_MODULE=canvas_account_admin_tools.settings.local
> sudo apt-get install xvfb
> python selenium_tests/regression_tests.py

Or for just one set of tests, for example:
> python selenium_tests/canvas_account_admin_tools/test_search.py

In PyCharm, if xvfb is installed already, you can run them through the Python unit test run config
(make sure the above environment settings are included)
"""

import unittest
import time

from os import path, makedirs

import HTMLTestRunner
from selenium_tests.account_admin.account_admin_is_dashboard_page_loaded_test import AccountAdminIsDasboardLoadedTest
from selenium_tests.course_info.course_info_is_search_page_loaded_test import CourseInfoIsSearchPageLoadedTest
from selenium_tests.course_info.course_info_search_test import CourseInfoSearchTest


date_timestamp = time.strftime('%Y%m%d_%H_%M_%S')

# This relative path should point to BASE_DIR/selenium_tests/reports
report_file_path = path.relpath('../reports')
if not path.exists(report_file_path):
    makedirs(report_file_path)
report_file_name = "course_info_test_report_{}.html".format(date_timestamp)
report_file_buffer = file(path.join(report_file_path, report_file_name), 'wb')
runner = HTMLTestRunner.HTMLTestRunner(
    stream=report_file_buffer,
    title='Course Info test suite report',
    description='Result of tests in {}'.format(__file__)
)

# course search - test the flow of the app from login to course search
dashboard_page_tests = unittest.TestLoader().loadTestsFromTestCase(AccountAdminIsDasboardLoadedTest)
course_info_initialize_testing = unittest.TestLoader().loadTestsFromTestCase(CourseInfoIsSearchPageLoadedTest)
course_info_search_testing = unittest.TestLoader().loadTestsFromTestCase(CourseInfoSearchTest)

# create a test suite combining the tests above
smoke_tests = unittest.TestSuite([dashboard_page_tests, course_info_initialize_testing, course_info_search_testing])

# run the suite
runner.run(smoke_tests)
# close test report file
report_file_buffer.close()
