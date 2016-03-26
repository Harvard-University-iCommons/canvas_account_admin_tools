from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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


        #TODO: #1. update locators on details PO to find xpath details,
        # # by ID isn't working for some reasons
        # Non-Working locator:
        # element = self.detail_page.get_input_field_for_non_editable_fields(
        #             'registrar_code_display')


        """
        Every field element has a span/input id so the test needs to check on
        the presence of a unique class element for non-editable fields.
        """

        #TODO: #2. refactor "find elements" and reusable locators to the PO
        #TODO: #3. loop through all the fields that are editable for this test

        # WORKING TEST
        # Tests that the specific field is non-editable
        element = self.driver.find_element_by_xpath(
            ".//*[@id='span-course-course_instance_id"
            "']").find_elements(*Locators.NON_EDITABLE_FIELD_CLASS_NAME)
        self.assertTrue(EC.presence_of_element_located(element))




