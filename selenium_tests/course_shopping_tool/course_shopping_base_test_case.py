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
        missing_required_var = None
        shopping_data = settings.SELENIUM_CONFIG['course_shopping']
        cls.username = shopping_data['user_HUID']
        cls.password = shopping_data['user_password']

        cls.canvas_base_dev_url = settings.SELENIUM_CONFIG.get(
            'canvas_base_url')
        cls.shopping_url = '{}{}'.format(
            cls.canvas_base_dev_url, shopping_data['relative_url'])

        if not (cls.username and cls.password):
            missing_required_var = 'shopping user credentials'

        if not cls.canvas_base_dev_url:
            missing_required_var = 'Canvas base URL'

        if not cls.shopping_url:
            missing_required_var = 'shopping tool relative URL'

        if missing_required_var:
            raise RuntimeError(
                'Missing {} in SELENIUM_CONFIG!'.format(missing_required_var))

        cls.shopping_page = CourseShoppingPageObject(cls.driver)
        cls.shopping_page.get(cls.shopping_url)

        # Verify if we already logged on, if not, do PIN logon
        if not cls.shopping_page.is_loaded():
            login_page = PinLoginPageObject(cls.driver)
            # Verify if we need to logon
            cls.driver.save_screenshot('pic1')
            if login_page.is_loaded():
                login_page.login_xid(cls.username, cls.password)
            else:
                raise RuntimeError(
                    'Could not determine if canvas main page loaded as'
                    ' expected; title element was found but did not'
                    ' contain expected text'
                )

        # adding more time for the shopping banner to appear
        
