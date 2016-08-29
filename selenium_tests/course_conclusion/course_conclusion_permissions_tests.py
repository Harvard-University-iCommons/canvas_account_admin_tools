from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.account_admin.account_admin_base_test_case import \
    AccountAdminBaseTestCase
from selenium_tests.course_conclusion.course_conclusion_base_test_case import \
    PERMISSIONS_ROLES
from selenium_tests.course_conclusion.page_objects\
    .course_conclusion_main_page import CourseConclusionMainPage


@ddt
class PermissionsTests(AccountAdminBaseTestCase):

    # TESTING PERMISSIONS OF THE COURSE CONCLUSION APP
    @data(*get_xl_data(PERMISSIONS_ROLES))
    @unpack
    def test_course_conclusion_permission(self, user_id, given_access):
        """
        This test masquerades as user in the spreadsheet, verifies that user
        sees the course conclusion card, and can click into the card
        """

        #  Masquerades as test user
        self.masquerade_page.masquerade_as(user_id)

        # Go to the Admin Console Dashboard
        self.driver.get(self.TOOL_URL)

        #  Test the visibility of Course Conclusion as masqueraded user
        if given_access == 'yes':

            self.masquerade_page.focus_on_tool_frame()

            # asserts that the course conclusion card appears on dashboard
            self.assertTrue(
                self.acct_admin_dashboard_page
                    .conclude_courses_button_is_displayed(),
                'User {} should see the course conclusion button on page but '
                'does not'.format(user_id)
            )

            # Click on course conclusion card and verify you get
            # into tool
            self.acct_admin_dashboard_page.select_conclude_courses_link()

            # Verify course conclusion main page loads
            course_conclusion_main_page = CourseConclusionMainPage(self.driver)

            main_window = self.driver.current_window_handle
            new_window = self.driver.window_handles[-1]

            #  The course conclusion tool opens up in a new window.  Need to
            #  account for the switch and switch back once assert is
            # completed.

            self.driver.switch_to_window(new_window)

            # Verifies the course conclusion page page is loaded
            self.assertTrue(course_conclusion_main_page.is_loaded())

            # Go back to main window after the course conclusion app loaded
            self.driver.switch_to_window(main_window)

        elif given_access == 'no':

            # asserts that user does not have access to the course conclusion
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
