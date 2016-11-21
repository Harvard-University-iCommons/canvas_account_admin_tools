from selenium_common.canvas.canvas_course_page_object import \
    CanvasCoursePage, Locators
from selenium_common.canvas.course_settings_page_object import CourseSettingsPage
from selenium_common.decorators import screenshot_on_test_exception
from selenium_tests.bulk_create.bulk_create_base_test_case \
    import BulkCreateBaseTestCase
from selenium_tests.bulk_create.page_objects.create_course_page import \
    CreateCoursePageObject
from selenium_tests.bulk_create.page_objects.index_page import \
    IndexPageObject


class CreateCourseInstanceTests(BulkCreateBaseTestCase):
    """
    Current Limitation with these tests:
    - Running these tests multiple times with the same course code will
      result in multiple rows in CourseManager database. For cleanup, use the
      script developed in TLT-2466.
    """

    @screenshot_on_test_exception
    def test_create_site_with_short_title(self):
        """
        This test uses the optional short title field in course creation.
        The course code on newly created Canvas site should just be the
        short title.
        """
        # TODO: Create 2 tests from this one and clean-up data after each test
        # (1) Randomize the course_title, to create CI and expect that we will
        #     not get the modal window
        # (2) Using same course_title, to get the modal window

        # If a course has course title, the course code is the short title.
        expected_course_code_text = self.test_data['course_short_title']

        self._test_create_site(
            self.test_data['course_code'],
            self.test_data['course_title'],
            self.test_data['course_short_title'],
            self.test_data['term'],
            expected_course_code_text)

    @screenshot_on_test_exception
    def test_create_site_without_short_title(self):
        """
        This test does not use the optional course short title as part of
        course creation.  The course code on the newly created Canvas site
        should just be "default ILE-prefix + course code"
        """
        expected_course_code_text = "ILE-{}".format(
            self.test_data['course_code'])

        self._test_create_site(
            self.test_data['course_code'],
            self.test_data['course_title'],
            '',  # simulates no short title entered in form
            self.test_data['term'],
            expected_course_code_text)

    def _test_create_site(self, course_code, course_title, course_short_title,
                          course_term, expected_course_code):
        """
        Common logic for testing site creation.
        """
        index_page = IndexPageObject(self.driver)
        create_new_ci = CreateCoursePageObject(self.driver)
        canvas_course = CanvasCoursePage(self.driver)
        canvas_settings = CourseSettingsPage(self.driver)

        # Go to the Course Site Creator Tool
        self.driver.get(self.base_url)

        # Switch to active frame
        canvas_course.focus_on_tool_frame()

        # Click on to Create new course link from Index page
        index_page.get_new_course_link()

        # Fill form with test data from settings and submit form
        create_new_ci.add_new_course_instance(
            course_code,
            course_title,
            course_short_title,
            course_term
        )

        # Verify confirmation modal window, if course for term and
        # course code was previously created, click Ok in modal window
        # before checking for success message
        if (create_new_ci.confirm_modal_visible()):
            # Click OK in modal window
            create_new_ci.click_confirmation_modal()

        # Verify course creation was successful
        self.assertTrue(create_new_ci.success_message_visible())

        # Click on the site link, which opens up in a new window
        create_new_ci.go_to_new_canvas_course()

        # Verify that Canvas site has been created
        self.assertTrue(canvas_course.is_loaded())

        # Verify the right Canvas course has been created
        # Click to go to Canvas Site Settings Page
        canvas_course.open_course_settings()
        self.assertTrue(canvas_settings.is_loaded())

        # Get the course code on the Canvas Site
        settings_course_code = canvas_settings.get_course_code()

        # Compare the expected_course_code with actual course code created
        # If a course has course title, the course code is the short title.
        self.assertEqual(settings_course_code, expected_course_code,
                         "Error: the course code on newly created Canvas site "
                         "does not match expected course code")
