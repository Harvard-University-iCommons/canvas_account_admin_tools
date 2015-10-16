import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_parent_page_object import CourseInfoParentPage
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject



class CourseInfoSearchTest(CourseInfoBaseTestCase):

    def test_course_search(self):
        """Check the course search functionality"""
        driver = self.driver
        parent_page = CourseInfoParentPage(driver)  # instantiate the tool
        search_page = CourseSearchPageObject(driver)

        search_page = parent_page.select_course_info_link()
        # driver.save_screenshot("screenshot.png")

        # select a school
        search_page.select_school("Divinity School")

        # submit a search term
        search_page.submit_search("7591")

        driver.save_screenshot("screenshot1.png")
        # self.assertIn("Bioethics, Law and the Life Sciences", driver.page_source,
        #               "Error: Expected search result to find course  '{}' ",
        #               "Bioethics, Law and the Life Sciences")

        body_text = self.driver.find_element_by_tag_name('body').text
        print body_text
        # Assert that the progress bar appears
        self.assertTrue("Search in progress" in body_text)


if __name__ == "__main__":
    unittest.main()