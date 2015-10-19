import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_parent_page_object import CourseInfoParentPage
from selenium_tests.course_info.page_objects.course_info_search_page_object import CourseSearchPageObject


class CourseInfoIsSearchPageLoadedTest(CourseInfoBaseTestCase):

    def test_is_loaded(self):
        """
        Verify  that the course info search page is loaded by checking against page title
        """
        driver = self.driver
        parent_page = CourseInfoParentPage(driver)
        search_page = CourseSearchPageObject(driver)

        # navigate to course info search page
        search_page = parent_page.select_course_info_link()
        element = search_page.get_page_title()
        page_title_text = "Find Course"
        self.assertEqual(element.text, page_title_text,
                         "Error: Wrong page. Expected page title is '{}' but "
                         "page title is returning '{}'".format(page_title_text, element.text))


if __name__ == "__main__":
    unittest.main()