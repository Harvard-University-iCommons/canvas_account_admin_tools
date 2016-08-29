from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

from selenium_tests.account_admin.account_admin_base_test_case import \
    AccountAdminBaseTestCase
from selenium_tests.search_people.search_people_base_test_case import \
    PERMISSIONS_ROLES
from selenium_tests.search_people.page_objects.search_people_base_page_object\
    import SearchPeoplePageObject


@ddt
class PermissionsTests(AccountAdminBaseTestCase):

    # TESTING PERMISSIONS OF SEARCH PEOPLE APP
    @data(*get_xl_data(PERMISSIONS_ROLES))
    @unpack
    def test_search_people_permission(self, user_id, given_access):
        """
        This test masquerades as user in the spreadsheet, verifies that user
        sees the search courses card in admin console and clicks into the tool
        """

        #  Masquerades as test user
        self.masquerade_page.masquerade_as(user_id)

        # Go to the Admin Console Dashboard
        self.driver.get(self.TOOL_URL)

        # Test the visibility of search people as a masqueraded user
        if given_access == 'yes':
            self.masquerade_page.focus_on_tool_frame()
            self.assertTrue(
                self.acct_admin_dashboard_page
                    .search_people_button_is_displayed(),
                'User {} should see the search people button on page, '
                'but does not'.format(user_id)
            )

            # Click on Search People link and verify the tool loads
            self.acct_admin_dashboard_page.select_search_people_link()
            search_people_main_page = SearchPeoplePageObject(self.driver)
            # Switch to new frame
            self.assertTrue(search_people_main_page.is_loaded())

        elif given_access == 'no':
            self.driver.get(self.TOOL_URL)
            self.assertFalse(
                self.acct_admin_dashboard_page
                    .search_people_button_is_displayed(),
                'User {} does not see the tool, but should.'.format(user_id))
        else:
            raise ValueError(
                'given_access column for user {} must be either "yes" or '
                '"no"'.format(user_id)
            )
