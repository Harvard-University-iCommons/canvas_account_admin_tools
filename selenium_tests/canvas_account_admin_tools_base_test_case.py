from urllib.parse import urljoin

from django.conf import settings

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object \
    import AccountAdminDashboardPage


class AccountAdminBaseTestCase(BaseSeleniumTestCase):

    @classmethod
    def setUpClass(cls):
        super(AccountAdminBaseTestCase, cls).setUpClass()

        cls.USERNAME = settings.SELENIUM_CONFIG['selenium_username']
        cls.PASSWORD = settings.SELENIUM_CONFIG['selenium_password']
        cls.CANVAS_BASE_URL = settings.SELENIUM_CONFIG['canvas_base_url']
        cls.TOOL_RELATIVE_URL = settings.SELENIUM_CONFIG['account_admin']['relative_url']
        cls.TOOL_URL = urljoin(cls.CANVAS_BASE_URL, cls.TOOL_RELATIVE_URL)

        cls.acct_admin_dashboard_page = AccountAdminDashboardPage(cls.driver)
        cls.acct_admin_dashboard_page.get(cls.TOOL_URL)
        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print('(User {} is already logged in)'.format(cls.USERNAME))

