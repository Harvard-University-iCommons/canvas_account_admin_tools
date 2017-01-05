from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.publish_courses.page_objects.main_page import MainPageObject


class PublishCoursesBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):
        super(PublishCoursesBaseTestCase, self).setUp()

        # instantiate
        self.main_page = MainPageObject(self.driver)

        # Test data for use in tests
        self.term = settings.SELENIUM_CONFIG['publish_courses']

        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to Publish Courses tool
        self.acct_admin_dashboard_page.select_publish_courses_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.main_page.is_loaded())

        #  Focus on tool frame
        self.main_page.focus_on_tool_frame()
