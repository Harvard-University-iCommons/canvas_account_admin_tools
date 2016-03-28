from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_detail_page_object \
    import  Locators


class CourseInfoDetailsNonEditTests(CourseInfoBaseTestCase):

    def setUp(self):
        super(CourseInfoDetailsNonEditTests, self).setUp()
        # Load a non-ILE course to validate non editable courses
        self._load_test_course()
        self.assertTrue(self.detail_page.is_loaded())


    def test_regular_course_not_editable(self):
        """
        verify non-SB/ILE courses cannot be edited
        """
        # Assert that the Save and Reset button are not present
        self.assertEquals(self.detail_page.is_locator_element_present
                          (Locators.RESET_FORM_BUTTON), False)
        self.assertEquals(self.detail_page.is_locator_element_present
                          (Locators.SAVE_FORM_BUTTON), False)

        # The span element exists only there if is a value in the field.
        # Limitation:  Each of the fields of the test site is
        # populated with a value. When testing a new course, note that
        # tests may break if field values are null.

        non_editable_fields = [
        'course_instance_id',
        'description',
        'instructors_display',
        'location',
        'meeting_time',
        'notes',
        'registrar_code_display',
        'sub_title',
        'term',
        'title'
        ]

        # The tests are validating against an exact match for the class
        # attribute of non-editable fields
        # (Editable fields also contain a "ng-binding" but it is always
        # accompanied by additional suffixes "ng-binding some_value",
        # which is not an exact match).
        expected_class_name = "ng-binding"


        for element in non_editable_fields:
            # assert exact class associated with non-editable fields
            # and also verifies that the field is not rendered as an input element
            self.assertEqual(self.detail_page.get_span_element_class(element),
                             expected_class_name)
            self.assertFalse(
                    self.detail_page.is_element_displayed_as_input_field(element))
