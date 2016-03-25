from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_detail_page_object \
    import CourseInfoDetailPageObject, Locators


class CourseInfoDetailsNonEditTests(CourseInfoBaseTestCase):

    def setUp(self):
        super(CourseInfoDetailsNonEditTests, self).setUp()
        #Load a non-ILE course to validate non editable courses
        self._load_test_course()
        self.assertTrue(self.detail_page.is_loaded())

    def test_regular_course_not_editable(self):
        """
        verify non-SB/ILE courses cannot be edited
        """

        #Assert that the Save and Reset button are not present
        self.assertEquals(self.detail_page.is_locator_element_present
                          (Locators.RESET_FORM_BUTTON), False)
        self.assertEquals(self.detail_page.is_locator_element_present
                          (Locators.SAVE_FORM_BUTTON), False)

        # assert that an editable field(ex:  title) element is present, but not editable
        # Note - this is WIP , not working yet.
        editable_field ='title'
        result = self.detail_page.get_input_field(editable_field)



