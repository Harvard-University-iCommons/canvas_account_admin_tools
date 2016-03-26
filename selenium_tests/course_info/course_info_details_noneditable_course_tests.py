from selenium.webdriver.support import expected_conditions as EC

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

        non_editable_fields = [
        'term',
        'registrar_code_display'
        ]
        # TODO: get the full list of fields to loop through

        # loops through each of the non-editable fields and looks for the
        # unique class element associated with non-editable fields
        for element in non_editable_fields:
            field_element = self.driver.find_element(
                *Locators.SPAN_ELEMENT_BY_FIELD_NAME(
                element)).find_elements(
                *Locators.NON_EDITABLE_FIELD_CLASS_NAME)

        # verifies that the fields are non-editable
        self.assertTrue(EC.presence_of_element_located(field_element))
