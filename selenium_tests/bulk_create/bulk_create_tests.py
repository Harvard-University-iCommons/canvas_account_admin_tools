from selenium_tests.bulk_create.bulk_create_base_test_case \
    import BulkCreateBaseTestCase
from selenium_tests.bulk_create.page_objects.course_selection_page import \
    CourseSelectionPageObject
from selenium_tests.bulk_create.page_objects.index_page import \
    IndexPageObject, Locators


class BulkCreateTests(BulkCreateBaseTestCase):

    def _load_bulk_create_tool(self):
        """
        Common code: This method loads up the bulk create tool.
        """
        self.index_page = IndexPageObject(self.driver)
        self.course_selection_page = CourseSelectionPageObject(self.driver)

        # Get base_url and switch frame whenever loading up bulk create tool
        self.driver.get(self.base_url)
        self.index_page.focus_on_tool_frame()

        self.assertTrue(self.index_page.is_loaded())
        self.index_page.select_term(self.test_data['term'])
        self.index_page.select_course_group(self.test_data['course_group'])
        self.index_page.create_canvas_sites()
        self.course_selection_page.select_template(self.test_data['template'])

    def test_course_selection(self):
        """
        Tests that a user accessing the bulk create tool can access the landing
        page, make selections from the dropdowns, proceed to the course
        selection page, and select courses and a template to enable course
        creation.
        """
        # Load up the tool as predefined
        self._load_bulk_create_tool()

        # Create button should be enabled and show text 'Create All'
        self.assertTrue(
            self.course_selection_page.is_create_all_button_enabled()
        )

        # select two courses from the datatable
        # we are not actually creating courses here, if we do
        # we'll need to change this
        self.course_selection_page.select_course(0)
        self.course_selection_page.select_course(1)

        # Create button should be enabled and show text 'Create All'
        self.assertTrue(
            self.course_selection_page.is_create_selected_button_enabled()
        )


    def test_course_with_registrar_code_display(self):

        """
        TLT-2522: Tests that "registrar_code_display" appears in the bulk
        create tool table, for a course that has a registrar_code display_value

        LIMITATION: This test checks against an element of a particular row and
        column in the bulk create table. If the data changes, it is possible
        that the test will fail.  However, this tightened test is marginally
        preferable and specific to simply checking that any elements that
        matches expected text in the table.

        """
        self._load_bulk_create_tool()
        expected_registrar_code = self.test_data_course1[
            'registrar_code_display']

        # This returns the text of a specific locator on bulk_create table
        registrar_code_element = self.driver.find_element(
                *Locators.COURSE_CODE_LOCATOR_R4_C3)
        actual_registrar_code = registrar_code_element.text

        self.assertEqual(expected_registrar_code, actual_registrar_code,
                         "Registrar code display does not match")


    def test_course_without_registrar_code_display(self):

        """
        TLT- 2522:  TLT-2522: Tests that "registrar_code" appears in the bulk
        create tool table, for a course does not have a registrar_code_display

        LIMITATION: This test checks against an element of a particular row and
        column in the bulk create table. If the data changes, it is possible
        that the test will fail.  However, this tightened test is more
        specific and marginally preferable and specific to simply checking
        that any elements that matches expected text in the table.

        """
        self._load_bulk_create_tool()
        expected_registrar_code = self.test_data_course2[
            'registrar_code_display']

        # This returns the text of a specific locator on bulk_create table
        registrar_code_element = self.driver.find_element(
                *Locators.COURSE_CODE_LOCATOR_R3_C3)
        actual_registrar_code = registrar_code_element.text

        self.assertEqual(expected_registrar_code, actual_registrar_code,
                         "Registrar code does not match")
