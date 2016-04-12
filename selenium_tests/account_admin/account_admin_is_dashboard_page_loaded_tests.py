from selenium_tests.account_admin.account_admin_base_test_case import AccountAdminBaseTestCase
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage


class AccountAdminIsDasboardLoadedTest(AccountAdminBaseTestCase):

    def test_is_account_admin_dashboard_page_loaded(self):

        """
        Check if the admin dashboard page is loaded
        """
        # initialize
        dashboard_page = AccountAdminDashboardPage(self.driver)
        self.assertTrue(dashboard_page.is_loaded())
        # The cross listing button should be displayed for the
        # selenium user in this test
        self.assertTrue(dashboard_page.cross_listing_button_is_displayed)
