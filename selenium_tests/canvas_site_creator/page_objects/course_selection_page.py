from selenium.webdriver.common.by import By
from selenium_common.webelements import Select

from selenium_tests.canvas_site_creator.page_objects.base_page_object \
    import BulkCreateBasePageObject


class Locators(object):
    COURSE_INSTANCE_TABLE = (By.ID, "courseInstanceDT")
    TEMPLATE_SELECT_DROPDOWN = (By.ID, "templateSelect")
    CREATE_BUTTON = (By.CSS_SELECTOR, "button[data-target='#confirmCreate']")
    COURSE_CHECKBOXES = (By.CSS_SELECTOR, "tbody input[type='checkbox']")


class CourseSelectionPageObject(BulkCreateBasePageObject):
    """
    bulk create step 2, select template and courses to create
    """
    page_loaded_locator = Locators.COURSE_INSTANCE_TABLE

    def select_template(self, template):
        select = Select(self.find_element(*Locators.TEMPLATE_SELECT_DROPDOWN))
        select.select_by_value(template)

    def select_course(self, index):
        """
        selects course selection checkbox in course list table by index
        (e.g. index=0 finds first checkbox in the table)
        """
        course_checkboxes = self.find_elements(*Locators.COURSE_CHECKBOXES)
        course_checkboxes[index].click()

    def is_create_all_button_enabled(self):
        """
        check to see if the create selected button is enabled.
        If a template is selected the button should be enabled.
        """
        create_button = self.find_element(*Locators.CREATE_BUTTON)
        return (create_button.is_enabled() and
                create_button.text == 'Create All')

    def is_create_selected_button_enabled(self):
        """
        check to see if the create selected button is enabled.
        If a template is selected the button should be enabled.
        """
        create_button = self.find_element(*Locators.CREATE_BUTTON)
        return (create_button.is_enabled() and
                create_button.text == 'Create Selected')
