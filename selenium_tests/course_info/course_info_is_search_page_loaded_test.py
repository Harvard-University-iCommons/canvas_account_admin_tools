import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage


class CourseInfoIsSearchPageLoadedTest(CourseInfoBaseTestCase):

    def test_is_loaded(self):
        """
        Verify  that the course info search page is loaded by checking against page title
        """
        parent_page = AccountAdminDashboardPage(self.driver)
        # navigate to course info search page
        search_page = parent_page.select_course_info_link()
        self.assertTrue(search_page.is_loaded())

if __name__ == "__main__":
    unittest.main()
