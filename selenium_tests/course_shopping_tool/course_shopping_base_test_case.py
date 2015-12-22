from django.conf import settings
from urlparse import urljoin
from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object import PinLoginPageObject
from selenium_tests.course_shopping_tool.page_objects.dashboard_page_object import DashboardPageObject

class CourseShoppingBaseTestCase(BaseSeleniumTestCase):
    """
    Course shopping base test case, all other tests will subclass
    this class
    """

    @classmethod
    def setUpClass(cls):
        """
        setup values for the tests
        """
        super(CourseShoppingBaseTestCase, cls).setUpClass()
        cls.USERNAME = settings.SELENIUM_CONFIG.get('shopping_user_HUID')
        cls.COURSE_ID = settings.SELENIUM_CONFIG.get('canvas_shopping_course_id')
        # new dev environment needs setup and configuration.
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('shopping_user_password')
        cls.CANVAS_BASE_DEV_URL = settings.SELENIUM_CONFIG.get('canvas_base_dev_url')
        cls.shopping_url = urljoin(
            settings.SELENIUM_CONFIG.get('canvas_base_dev_url'),
            settings.SELENIUM_CONFIG.get('canvas_shopping_relative_url'))
        #  Login to tool index page
        cls.index_page = DashboardPageObject(cls.driver)
        cls.index_page.get(cls.CANVAS_BASE_DEV_URL)

        login_page = PinLoginPageObject(cls.driver)

        # Verify that login page is loaded
        if login_page.is_loaded():
            login_page.login_huid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)
        # Verifies that the index dashboard page is loaded after logging in
        if cls.index_page.is_loaded():
            cls.driver.get(cls.shopping_url)

