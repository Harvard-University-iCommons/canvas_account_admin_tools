import unittest

from selenium_tests.course_info.course_info_base_test_case import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_parent_page_object import CourseInfoParentPage


class CourseInfoIsLoadedTest(CourseInfoBaseTestCase):

    def test_is_page_loaded(self):

        """Check that page is loaded by checking against site title"""
        driver = self.driver
        page = CourseInfoParentPage(driver)  # instantiate

        element = page.get_page_title()
        page_title_text = "Administration Tasks"
        print "Verifying page title..."
        self.assertEqual(element.text, page_title_text,
                         "Error: Wrong page. Expected page title is '{}' but "
                         "page title is returning '{}'".format(page_title_text, element.text))

        # # verify course info block
        # element = page.get_course_info_link()
        # print(" link text obtained is  %s" % element.text)
        # link_text = 'Course Information \n ' \
        #             'Search for course information'
        #
        # self.assertEqual(element.text, link_text,
        #                  "Error: Wrong page. Expected Course Info link '{}' but "
        #                  "page is returning '{}'".format(link_text, element.text))

    def test_is_link_present(self):
        """Check that Course Info link  is loaded by checking against Link text"""
        driver = self.driver
        page = CourseInfoParentPage(driver)  # instantiate

        # verify course info block
        element = page.get_course_info_link()
        print(" link text obtained is 111 %s" % element.text)

        link_text = 'Course Information'
        print(" link 222= %s" %link_text)
        print("----")
        self.assertTrue(link_text in element.text,
                         "Error: Wrong page. Expected Course Info link '{}' but "
                         "page is returning '{}'".format(link_text, element.text))


if __name__ == "__main__":
    unittest.main()