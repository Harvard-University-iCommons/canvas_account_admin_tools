from os.path import abspath, dirname, join
from urlparse import urljoin

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.publish_courses.page_objects.main_page import MainPageObject


# TEST_DATA_CROSS_LISTING_MAPPINGS = join(dirname(abspath(__file__)),
#     'test_data', '.xlsx')


class PublishCoursesBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):
        super(PublishCoursesBaseTestCase, self).setUp()

        # instantiate
        self.main_page = MainPageObject(self.driver)

        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to Publish Courses tool
        self.acct_admin_dashboard_page.select_publish_courses_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.main_page.is_loaded())
