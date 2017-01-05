from selenium_tests.publish_courses.publish_courses_base_test_case import \
    PublishCoursesBaseTestCase
from selenium_tests.publish_courses.page_objects.main_page import \
    MainPageObject

from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation


class PublishCoursesTests(PublishCoursesBaseTestCase):

    def test_publish_courses(self):
        """TLT-1805: This test case goes through the workflow of publishing
        all courses in a specific term using the Publish Courses tool """

        main_page = MainPageObject(self.driver)

        #  Select a term from the term dropdown
        term_with_unpublished_courses = self.term['test_terms'][
            'term_with_unpublished_courses']
        main_page.select_term(term_with_unpublished_courses)

        # Setup: Set the initial state of courses to unpublish first,
        # to ensure that the publish functionality can be tested.
        self.bulk_unpublish_canvas_sites()

        #  Check that Publish All button is enabled
        self.assertTrue(main_page.is_publish_all_button_enabled())

        #  Click on Publish all button
        main_page.publish_courses()

        #  Verify that a confirmation appears on screen
        self.assertTrue(main_page.result_message_visible())

        #  Setting the course state back to unpublished as part of cleanup.
        self.bulk_unpublish_canvas_sites()

    def test_cannot_publish_courses(self):
        """ TLT-1805 -- This test case verifies that the "publish all" button
        is disabled in a term where all courses are published"""

        main_page = MainPageObject(self.driver)

        #  Select a term from the term dropdown
        term_with_all_published_courses = self.term['test_terms'][
            'term_with_all_published_courses']
        main_page.select_term(term_with_all_published_courses)

        #TODO: Cannot assume that the term will always be in the published
        # state. Probably best to set all courses to publish first before
        # running this test.

        #  Check that Publish All button is enabled
        self.assertFalse(main_page.is_publish_all_button_enabled())

    def bulk_unpublish_canvas_sites(self):
        """
        This is a setup and cleanup method to unpublish courses in a term
        """
        # Get term information from Settings
        op_config = self.term['op_config']

        # Bulk update courses based on parameter passed in op_config
        op = BulkCourseSettingsOperation(op_config)
        op.execute()
