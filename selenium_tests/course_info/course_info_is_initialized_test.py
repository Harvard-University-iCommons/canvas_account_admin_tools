import unittest
from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_parent_page_object import CourseInfoParentPage


class CourseInfoIsInitializedTest(CourseInfoBaseTestCase):

    def test_is_page_loaded(self):

        """
        Check if page is loaded
        """
        driver = self.driver
        # initialize
        page = CourseInfoParentPage(driver)
        page.is_loaded()

    def test_is_link_present(self):
        """
        Check that Course Info link is loaded by checking against Link text
        """
        driver = self.driver
        page = CourseInfoParentPage(driver)

        # verify that the course info block is present
        course_info_link = page.get_course_info_link()
        link_text = 'Course Information'

        self.assertTrue(link_text in course_info_link.text,
                        "Error: Wrong page. Expected Course Info link '{}' but "
                        "page is returning '{}'".format(link_text, course_info_link.text))

if __name__ == "__main__":
    unittest.main()