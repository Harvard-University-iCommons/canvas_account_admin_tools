from selenium.webdriver.support import expected_conditions as EC

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_detail_page_object \
    import  Locators



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
        # Assert that the Save and Reset button are not present
        self.assertEquals(self.detail_page.is_locator_element_present
                          (Locators.RESET_FORM_BUTTON), False)
        self.assertEquals(self.detail_page.is_locator_element_present
                          (Locators.SAVE_FORM_BUTTON), False)


        """TLT-2523: Every field has a span/input id regardless of whether
        the field is editable, so tests cannot rely on the presence of an
        span/input id.  The tests are validating against a unique class
        element for non-editable fields
        """

        # The span element exists only there is a value in the field.
        # Limitation:  Each of the fields of the test site is
        # populated with a value. When testing a new course, note that
        # tests may break if field values are null.

        non_editable_fields = [
        'course_instance_id',
        # 'departments',
        'description',
        'instructors_display',
        'location',
        'meeting_time',
        # 'notes',
        'registrar_code_display',
        'sub_title',
        'term',
        'title'
        ]

        # loops through each of the non-editable fields and looks for the
        # unique class element associated with non-editable fields
        expected_class_name = "ng-binding"
        for element in non_editable_fields:
            self.assertEqual(self.detail_page.get_span_element_class(element),
                             expected_class_name)


