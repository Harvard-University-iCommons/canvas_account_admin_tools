from django.conf import settings
from urlparse import urljoin

from selenium_common.base_test_case import BaseSeleniumTestCase
from selenium_common.pin.page_objects.pin_login_page_object \
    import PinLoginPageObject

from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object \
    import AccountAdminDashboardPage
from selenium_tests.cross_listing.page_objects.cross_listing_main_page \
    import MainPageObject


class CrossListingBaseTestCase(BaseSeleniumTestCase):

    @classmethod
    def setUpClass(cls):
        super(CrossListingBaseTestCase, cls).setUpClass()

        cls.USERNAME = settings.SELENIUM_CONFIG['selenium_username']
        cls.PASSWORD = settings.SELENIUM_CONFIG['selenium_password']

        cls.CANVAS_BASE_URL = settings.SELENIUM_CONFIG['canvas_base_url']
        cls.TOOL_RELATIVE_URL = settings.SELENIUM_CONFIG['account_admin']['relative_url']
        cls.TOOL_URL = urljoin(cls.CANVAS_BASE_URL, cls.TOOL_RELATIVE_URL)

        cls.account_admin_dashboard_page = AccountAdminDashboardPage(cls.driver)
        cls.account_admin_dashboard_page.get(cls.TOOL_URL)
        login_page = PinLoginPageObject(cls.driver)
        if login_page.is_loaded():
            login_page.login_xid(cls.USERNAME, cls.PASSWORD)
        else:
            print '(User {} already logged in to PIN)'.format(cls.USERNAME)

        cls.index_page = MainPageObject(cls.driver)

    def setUp(self):
        super(CrossListingBaseTestCase, self).setUp()

        # initialize
        if not self.account_admin_dashboard_page.is_loaded():
            self.account_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to cross-list tool
        self.account_admin_dashboard_page.select_cross_listing_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.index_page.is_loaded())
