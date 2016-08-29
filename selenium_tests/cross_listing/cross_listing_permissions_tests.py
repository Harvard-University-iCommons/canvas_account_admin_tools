from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.account_admin.account_admin_base_test_case import \
    AccountAdminBaseTestCase
from selenium_tests.cross_listing.cross_listing_base_test_case import \
    PERMISSIONS_ROLES
from selenium_tests.cross_listing.page_objects.cross_listing_main_page import\
    MainPageObject


@ddt
class PermissionsTests(AccountAdminBaseTestCase):

    # TESTING PERMISSIONS OF CROSS LISTING TOOL
    @data(*get_xl_data(PERMISSIONS_ROLES))
    @unpack
    def test_cross_listing_permission(self, user_id, given_access):
        """
        This test masquerades as user in the spreadsheet, verifies that user
        sees the cross-listing card, and can click into the crosslisting card
        """

        #  Masquerades as test user
        self.masquerade_page.masquerade_as(user_id)

        # Go to the Admin Console Dashboard
        self.driver.get(self.TOOL_URL)

        # Test the visibility of the cross-listing button as masqueraded user
        if given_access == 'yes':

            self.masquerade_page.focus_on_tool_frame()

            # asserts that the cross-listing card appears on dashboard
            self.assertTrue(
                self.acct_admin_dashboard_page
                    .cross_listing_button_is_displayed(),
                'User {} should see the class roster button on page but '
                'does not'.format(user_id)
            )

            # Click on cross-listing card and verify you get into tool
            self.acct_admin_dashboard_page.select_cross_listing_link()

            # Verify cross-listing main page loads
            cross_listing_main_page = MainPageObject(self.driver)
            self.assertTrue(cross_listing_main_page.is_loaded())

        elif given_access == 'no':

            # asserts that user does not have access to the cross-listing
            # card on dashboard
            self.assertFalse(
                self.acct_admin_dashboard_page
                    .cross_listing_button_is_displayed(), 'User {} does '
                'not see the tool, but should.'.format(user_id))
        else:
            raise ValueError(
                'given_access column for user {} must be either "yes" or '
                '"no"'.format(user_id)
            )
