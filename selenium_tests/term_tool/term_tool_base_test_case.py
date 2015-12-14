from urlparse import urljoin

from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object import PinLoginPageObject
from selenium_tests.term_tool.page_objects.term_tool_shopping_exclude_page_object \
    import TermToolShoppingExcludePageObject


class TermToolBaseTestCase(BaseSeleniumTestCase):
    """Term Tool base test case, all other tests will subclass this class"""

    @classmethod
    def setUpClass(cls):
        """
        setup values for the tests
        """
        super(TermToolBaseTestCase, cls).setUpClass()
        cls.USERNAME = settings.SELENIUM_CONFIG.get('selenium_username')
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('selenium_password')
        cls.TERM_TOOL_BASE_URL = settings.SELENIUM_CONFIG.get('term_tool_base_url')
        cls.TERM_TOOL_RELATIVE_URL = settings.SELENIUM_CONFIG.get('term_tool_relative_url')
        cls.TOOL_URL = urljoin(cls.TERM_TOOL_BASE_URL, cls.TERM_TOOL_RELATIVE_URL)

        #  Login to Term Tool Index Page
        cls.term_tool_index_page = TermToolShoppingExcludePageObject(cls.driver)
        cls.term_tool_index_page.get(cls.TOOL_URL)
        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)
