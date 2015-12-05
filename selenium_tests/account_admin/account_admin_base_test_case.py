from urlparse import urljoin

from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object import PinLoginPageObject
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage


class AccountAdminBaseTestCase(BaseSeleniumTestCase):
    """
    Bulk Create base test case, all other tests will subclass this class
    """
    @classmethod
    def setUpClass(cls):
        """
        setup values for the tests
        """
        super(AccountAdminBaseTestCase, cls).setUpClass()

        driver = cls.driver
        cls.USERNAME = settings.SELENIUM_CONFIG.get('selenium_username')
        cls.PASSWORD = settings.SELENIUM_CONFIG.get('selenium_password')
        cls.CANVAS_BASE_URL = settings.SELENIUM_CONFIG.get('canvas_base_url')
        cls.TOOL_RELATIVE_URL = settings.SELENIUM_CONFIG.get('account_admin_relative_url')
        cls.TOOL_URL = urljoin(cls.CANVAS_BASE_URL, cls.TOOL_RELATIVE_URL)

        cls.acct_admin_dashboard_page = AccountAdminDashboardPage(driver)
        cls.acct_admin_dashboard_page.get(cls.TOOL_URL)
        login_page = PinLoginPageObject(driver)
        if login_page.is_loaded():
            print " logging the user in"
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)

