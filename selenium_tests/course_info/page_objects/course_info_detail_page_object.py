from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.course_info.page_objects.course_info_base_page_object \
    import CourseInfoBasePageObject


class Locators(object):
    EDIT_FORM_BUTTON = (By.ID, "course-details-form-edit")
    PEOPLE_LINK = (By.ID, "course-details-people-tab-id")
    MAIN_TAG = (By.CSS_SELECTOR, "main.course-info-details-page")
    RESET_FORM_BUTTON = (By.ID, "course-details-form-reset")
    SUBMIT_FORM_BUTTON = (By.ID, "course-details-form-submit")
    SUBMIT_SUCCESS_MSG = (By.ID, "alert-success-update-succeeded")

    @classmethod
    def INPUT_BY_FIELD_NAME(cls, field_name):
        """
        returns a locator for an input field for a course instance record
        field name (e.g. title, sub_title, description)
        """
        return By.ID, 'input-course-{}'.format(field_name)


class CourseInfoDetailPageObject(CourseInfoBasePageObject):
    page_loaded_locator = Locators.MAIN_TAG

    def enter_text_in_input_field(self, field_name, value):
        self._wait_for_input_field_to_be_visible(field_name)
        input = self.find_element(*Locators.INPUT_BY_FIELD_NAME(field_name))
        input.clear()
        input.send_keys(value)

    def get_input_field_value(self, field_name):
        self._wait_for_input_field_to_be_visible(field_name)
        input = self.find_element(*Locators.INPUT_BY_FIELD_NAME(field_name))
        return input.get_attribute('value')

    def is_element_displayed_as_input_field(self, field_name):
        try:
            is_displayed = self.find_element(*Locators.INPUT_BY_FIELD_NAME(
                    field_name)).is_displayed()
            return is_displayed
        except NoSuchElementException:
            return False

    def verify_buttons_to_edit_page_are_present(self):
        """Return true if the button appears on page"""
        try:
            return self.find_element(*Locators.EDIT_FORM_BUTTON).is_displayed()
        except NoSuchElementException:
            return False

    def edit_form(self):
        """Find and click on the Edit button"""
        self.find_element(*Locators.EDIT_FORM_BUTTON).click()

    def go_to_people_page(self):
        self.find_element(*Locators.PEOPLE_LINK).click()

    def submit_form(self):
        """Find and click on the submit button"""
        self.find_element(*Locators.SUBMIT_FORM_BUTTON).click()

    def reset_form(self):
        self.find_element(*Locators.RESET_FORM_BUTTON).click()

    def submit_was_successful(self):
        """ Returns true if the success message is shown after """
        try:
            WebDriverWait(self._driver, 10).until(lambda s: s.find_element(
                *Locators.SUBMIT_SUCCESS_MSG).is_displayed())
        except TimeoutException:
            return False
        return True

    def _wait_for_input_field_to_be_visible(self, field_name):
        # only want to access input elements once the values are loaded from the
        # server (which in this case means the spinner disappears and the input
        # element becomes visible)
        WebDriverWait(self._driver, 10).until(lambda s: s.find_element(
            *Locators.INPUT_BY_FIELD_NAME(field_name)).is_displayed())
