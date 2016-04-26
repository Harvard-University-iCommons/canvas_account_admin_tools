from selenium_tests.canvas_account_admin_tools_base_test_case \
    import AccountAdminBaseTestCase
from selenium_tests.cross_listing.page_objects.cross_listing_main_page \
    import MainPageObject


class CrossListingBaseTestCase(AccountAdminBaseTestCase):

    def setUp(self):
        super(AccountAdminBaseTestCase, self).setUp()

        # instantiate
        self.index_page = MainPageObject(self.driver)

        # initialize
        if not self.acct_admin_dashboard_page.is_loaded():
            self.acct_admin_dashboard_page.get(self.TOOL_URL)

        # navigate to cross-list tool
        self.acct_admin_dashboard_page.select_cross_listing_link()

        # check if page is loaded (which will also set the focus on the tool)
        self.assertTrue(self.index_page.is_loaded())
