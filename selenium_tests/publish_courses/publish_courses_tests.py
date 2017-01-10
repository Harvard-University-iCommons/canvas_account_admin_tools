from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation

from selenium_common.canvas.canvas_course_page_object import CanvasCoursePage

from selenium_tests.publish_courses.publish_courses_base_test_case import \
    PublishCoursesBaseTestCase
from selenium_tests.publish_courses.page_objects.main_page import \
    MainPageObject


class PublishCoursesTests(PublishCoursesBaseTestCase):

    def test_publish_courses(self):
        """TLT-1805: This test case goes through the workflow of publishing
        all courses in a specific term using the Publish Courses tool """

        main_page = MainPageObject(self.driver)

        #  Select a term from the term dropdown
        term_with_unpublished_courses = self.term['test_terms'][
            'term_with_unpublished_courses']
        main_page.select_term(term_with_unpublished_courses)

        # If the Publish Courses button is enabled, click on it.
        if main_page.is_publish_all_button_enabled():
            main_page.publish_courses()
        else:
            #  If "Publish all" button is not enabled, unpublish courses
            #  first to ensure that the publish functionality can be tested.
            self.bulk_unpublish_canvas_sites()

            #  Refresh the page to see the changes
            self.refresh_page(term_with_unpublished_courses)

            #  Verify that the Publish Button is clickable
            self.assertTrue(main_page.is_publish_all_button_enabled())
            #  Click on "Publish all" button
            main_page.publish_courses()

        #  Verify that a confirmation appears on screen
        self.assertTrue(main_page.result_message_visible())

        #  Go to a test course to spotcheck
        self.driver.get(self.test_course_url)

        # Verify that the Canvas site is now published
        canvas_course = CanvasCoursePage(self.driver)
        self.assertFalse(canvas_course.is_canvas_site_unpublished())

        #  Set course state back to unpublished as part of test cleanup.
        self.bulk_unpublish_canvas_sites()

    def test_cannot_publish_courses(self):
        """ TLT-1805 -- This test case verifies that the "publish all" button
        is disabled in a term where all courses are published"""

        main_page = MainPageObject(self.driver)

        #  Select a term from the term dropdown
        term_with_all_published_courses = self.term['test_terms'][
            'term_with_all_published_courses']
        main_page.select_term(term_with_all_published_courses)

        # If there are courses not yet published, publish it now.
        if main_page.is_publish_all_button_enabled():
            main_page.publish_courses()
            #  Refresh page to see the change
            self.refresh_page(term_with_all_published_courses)
            #  "Publish All" Button should be disabled
            self.assertFalse(main_page.is_publish_all_button_enabled())
        # If courses are published, the "Publish All" button should be disabled.
        else:
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

    def refresh_page(self, term):
        # Refresh page
        self.driver.refresh()
        # Go back to publish courses
        self.acct_admin_dashboard_page.select_publish_courses_link()
        # Go select the term
        self.main_page.select_term(term)

    def site_is_unpublished(self):
        self.driver.get(self.test_course_url)
        canvas_course = CanvasCoursePage(self.driver)
        canvas_course.is_canvas_site_unpublished()
