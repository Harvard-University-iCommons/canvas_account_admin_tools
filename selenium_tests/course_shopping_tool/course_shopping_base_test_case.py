from django.conf import settings
from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject
from selenium_tests.course_shopping_tool.page_objects.shopping_page_object \
    import CourseShoppingPageObject

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
        shopping_data = settings.SELENIUM_CONFIG['course_shopping']
        cls.USERNAME = shopping_data['user_HUID']
        cls.PASSWORD = shopping_data['user_password']

        cls.CANVAS_BASE_DEV_URL = \
            settings.SELENIUM_CONFIG.get('canvas_base_url')
        cls.shopping_url =  '{}{}'.format(
            cls.CANVAS_BASE_DEV_URL,shopping_data['relative_url'])
        cls.shopping_page = CourseShoppingPageObject(cls.driver)
        cls.shopping_page.get(cls.shopping_url)

        # Verify if we already logged on, if not, do PIN logon
        if not cls.shopping_page.is_loaded():
            login_page = PinLoginPageObject(cls.driver)
            # Verify if we need to logon
            if login_page.is_loaded():
                login_page.login_huid(cls.USERNAME, cls.PASSWORD)
            else:
                raise RuntimeError(
                    'Could not determine if canvas main page loaded as'
                    ' expected;title element was found but did not'
                     'contain expected text'
                )
