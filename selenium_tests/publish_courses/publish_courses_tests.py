from selenium_tests.publish_courses.publish_courses_base_test_case import \
    PublishCoursesBaseTestCase
from selenium_tests.publish_courses.page_objects.main_page import \
    MainPageObject


class PublishCoursesTests(PublishCoursesBaseTestCase):

    def test_publishing_courses(self):
        """TLT-1805: This test case goes through the workflow of publishing
        all courses in a specific term using the Publish Courses tool """

        main_page = MainPageObject(self.driver)

        #  Select a term from the term dropdown
        term_with_unpublished_courses = self.test_data[
            'term_with_all_published_courses']
        main_page.select_term(term_with_unpublished_courses)

        #  Check that Publish All button is enabled
        self.assertTrue(main_page.is_publish_all_button_enabled())

        #  Click on Publish all button
        main_page.publish_courses()

        #  Verify that a confirmation appears on screen
        self.assertTrue(main_page.result_message_visible())

        # TODO: cleanup - un-publish all courses for the term

    def test_cannot_publish_courses(self):
        """ TLT-1805 -- This test case verifies that the "publish all" button
        is disabled in a term where all courses are published"""

        main_page = MainPageObject(self.driver)

        #  Select a term from the term dropdown
        term_with_all_published_courses = self.test_data[
                                          'term_with_all_published_courses']
        main_page.select_term(term_with_all_published_courses)

        #  Select a term from the term dropdown
        main_page.select_term(term_with_all_published_courses)

        #  Check that Publish All button is enabled
        self.assertFalse(main_page.is_publish_all_button_enabled())
