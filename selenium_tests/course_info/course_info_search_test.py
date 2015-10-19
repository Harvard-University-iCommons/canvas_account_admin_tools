import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_parent_page_object import CourseInfoParentPage
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject, \
    CourseSearchPageLocators
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class CourseInfoSearchTest(CourseInfoBaseTestCase):

    def test_course_search(self):
        """verify the course search functionality"""
        driver = self.driver
        # initialize
        parent_page = CourseInfoParentPage(driver)
        search_page = CourseSearchPageObject(driver)
        # navigate to course info page
        search_page = parent_page.select_course_info_link()

        # select a school, year, term and  course type
        search_page.select_school("Divinity School")
        search_page.select_year("2014")
        search_page.select_term("Spring")
        search_page.select_course_type("Only courses without sites")

        # submit a search term, a course instance id in this case
        search_page.submit_search("339331")

        try:
            WebDriverWait(driver, 30).until(lambda s: s.find_element(
                *CourseSearchPageLocators.COURSE_RESULTS_TABLE).is_displayed())
        except TimeoutException:
            return False

        body_text = self.driver.find_element_by_tag_name('body').text
        print(body_text)

        # Verify that search results contains the course
        self.assertTrue("Latin Paleography and Manuscript Culture: Seminar" in body_text)


if __name__ == "__main__":
    unittest.main()
