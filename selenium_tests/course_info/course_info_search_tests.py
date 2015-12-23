import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.account_admin.page_objects.account_admin_dashboard_page_object import AccountAdminDashboardPage
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageLocators
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class CourseInfoSearchTest(CourseInfoBaseTestCase):

    def test_course_search(self):
        """verify the course search functionality"""
        # initialize
        parent_page = AccountAdminDashboardPage(self.driver)
        # navigate to course info page
        parent_page.select_course_info_link()

        # check if page is loaded(which will also set the focus on the tool), before selecting search terms
        search_page = CourseSearchPageObject(self.driver)
        search_page.is_loaded()

        # select a school, year, term and  course type
        search_page.select_school("Divinity School")
        search_page.select_year("2014")
        search_page.select_term("Spring")
        search_page.select_course_type("Only courses without sites")

        # submit a search term, a course instance id in this case
        search_page.submit_search("339331")

        try:
            WebDriverWait(self.driver, 30).until(lambda s: s.find_element(
                *CourseSearchPageLocators.COURSE_RESULTS_TABLE).is_displayed())
        except TimeoutException:
            return False

        body_text = self.driver.find_element_by_tag_name('body').text

        # Verify that search results contains the course
        self.assertTrue("Latin Paleography and Manuscript Culture: Seminar" in body_text)


if __name__ == "__main__":
    unittest.main()
