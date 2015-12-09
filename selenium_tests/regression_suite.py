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
import os

from selenium_common import HTMLTestRunner


def main():

    date_timestamp = time.strftime('%Y%m%d_%H_%M_%S')

    # This relative path should point to BASE_DIR/selenium_tests/reports
    report_file_path = os.path.relpath('./reports')
    if not os.path.exists(report_file_path):
        os.makedirs(report_file_path)
    report_file_name = "course_info_test_report_{}.html".format(date_timestamp)
    report_file_obj = file(os.path.join(report_file_path, report_file_name), 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
        stream=report_file_obj,
        title='Course Info test suite report',
        description='Result of tests in {}'.format(__file__)
    )

    suite = unittest.defaultTestLoader.discover(
        os.path.abspath(os.path.dirname(__file__)),
        pattern = '*_tests.py',
        top_level_dir=os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..'))
    )

    # run the suite
    runner.run(suite)
    # close test report file
    report_file_obj.close()

if __name__ == "__main__":
    main()

