import unittest
# from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
# from selenium_tests.course_info.page_objects.course_info_parent_page_object import CourseInfoParentPage
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

    def test_is_course_info_link_present(self):
        """
        Check that Course Info link is loaded by checking against Link text
        """
        page = AccountAdminDashboardPage(self.driver)

        # verify that the course info block is present
        self.assertTrue(page.is_course_info_block_present())


if __name__ == "__main__":
    unittest.main()
