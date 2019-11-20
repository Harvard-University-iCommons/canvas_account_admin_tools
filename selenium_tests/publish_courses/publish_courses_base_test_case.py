from django.conf import settings
from urllib.parse import urljoin

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.publish_courses.page_objects.main_page import MainPageObject


class PublishCoursesBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):
        super(PublishCoursesBaseTestCase, self).setUp()

        #  Test course URL
        self.base_url = settings.SELENIUM_CONFIG['canvas_base_url']
        self.test_course_relative_url = settings.SELENIUM_CONFIG[
            'publish_courses']['test_course']['relative_url']
        self.test_course_url = urljoin(self.base_url,
                                    self.test_course_relative_url)

        # Test data for use in tests
        self.test_settings = settings.SELENIUM_CONFIG['publish_courses']

        # instantiate
        self.main_page = MainPageObject(self.driver)

        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to Publish Courses tool
        self.acct_admin_dashboard_page.select_publish_courses_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.main_page.is_loaded())


