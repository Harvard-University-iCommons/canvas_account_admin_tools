from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject
from selenium_tests.course_shopping_tool.page_objects.index_page_page_object \
    import IndexPageObject


class CourseShoppingBaseTestCase(BaseSeleniumTestCase):
    """Course shopping base test case, all other tests will subclass
    this class"""

    @classmethod
    def setUpClass(cls):
        """
        setup values for the tests
        """
        super(CourseShoppingBaseTestCase, cls).setUpClass()
        cls.USERNAME = settings.SELENIUM_CONFIG.get('new_dev_selenium_user')
        # new dev environment needs setup and configuration.
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('selenium_password')
        cls.CANVAS_BASE_DEV_URL = settings.SELENIUM_CONFIG.get(
            'canvas_base_dev_url')
        #  Login to tool index page
        cls.shopping_index_page = IndexPageObject(cls.driver)
        cls.shopping_index_page.get(cls.CANVAS_BASE_DEV_URL)
        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)
        # Verifies that the index page is loaded after logging in
        cls.shopping_index_page.is_loaded()
