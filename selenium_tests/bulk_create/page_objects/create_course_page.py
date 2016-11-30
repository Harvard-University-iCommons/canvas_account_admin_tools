from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


from selenium_tests.bulk_create.page_objects.base_page_object \
    import BulkCreateBasePageObject


class Locators(object):
    CODE_TYPE_DROPDOWN = (By.ID, "course-code-type")
    COURSE_CODE = (By.ID, "course-code")
    COURSE_TITLE = (By.ID, "course-title")
    CREATE_NEW_COURSE_BUTTON = (By.ID, "create-course-instance")
    MODAL_CONFIRM_BUTTON = (By.ID, "existing-course-modal-confirm")
    SHORT_TITLE = (By.ID, "course-short-title")
    SUCCESS_MSG = (By.ID, "success-msg")
    TERM_CODE = (By.ID, "course-term")
    # lots of problems with CSS locators in selenium webdriver; this one
    # works as currently there should only be one row in table, and one link
    # in that row
    SITE_FIELD = (By.CSS_SELECTOR, "#new-course-info-container tbody a")


class CreateCoursePageObject(BulkCreateBasePageObject):
    page_loaded_locator = Locators.TERM_CODE

    def add_new_course_instance(self,
                                course_code,
                                course_title,
                                course_short_title,
                                term):
        """
        This function will fill the form and button click to create the
        course
        """

        self.get_course_code(course_code)
        self.get_course_title(course_title)
        self.get_short_title(course_short_title)
        self.get_term(term)

        add_course_link = self.find_element(*Locators.CREATE_NEW_COURSE_BUTTON)
        if add_course_link.is_enabled():
            add_course_link.click()

    def get_term(self, term_code):
        """
        Select the term from the dropdown
        """
        # adding an explicit wait as there is some flakiness in one of the tests
        # sporadically failing when the terms have not loaded on page.
        WebDriverWait(self._driver, 30).until(
                EC.visibility_of_element_located(Locators.TERM_CODE))

        element_select = self.find_element(*Locators.TERM_CODE)
        selenium_select = Select(element_select)
        selenium_select.select_by_visible_text(term_code)
        return selenium_select

    def get_course_title(self, course_title):
        """
        Fill in the course title
        """
        element = self.find_element(*Locators.COURSE_TITLE)
        element.clear()
        element.send_keys(course_title)
        return element

    def get_short_title(self, course_short_title):
        """
        Fill in the short tile
        """
        element = self.find_element(*Locators.SHORT_TITLE)
        element.clear()
        element.send_keys(course_short_title)
        return element

    def get_course_code(self, course_code):
        """
        Select ILE from the dropdown and
        fill in the course code (registrar code) in the textbox
        """
        element_select = self.find_element(*Locators.CODE_TYPE_DROPDOWN)
        selenium_select = Select(element_select)
        selenium_select.select_by_value("ILE")
        element = self.find_element(*Locators.COURSE_CODE)
        element.clear()
        element.send_keys(course_code)
        return element

    def success_message_visible(self):
        """
        Wait for the success message to be visible before time-out
        """
        try:
            WebDriverWait(self._driver, 60).until(
                EC.visibility_of_element_located(Locators.SUCCESS_MSG)
            )
        except TimeoutException:
            return False
        return True

    def confirm_modal_visible(self):
        """
        Look for the modal window, if previous course instance for the
        school, term and course code has already been created

        Note of possible failure:
        Modal window might fail to display within time limit,
        (currently set to 10s), possibly due to slowness with connecting
        with the back-end or the processing of the number of rows found on db.
        """
        try:
            self.find_element(*Locators.MODAL_CONFIRM_BUTTON)
        except NoSuchElementException:
            return False
        return True

    def click_confirmation_modal(self):
        """
        Click OK in the modal window
        """
        element = self.find_element(*Locators.MODAL_CONFIRM_BUTTON)
        element.click()

    def go_to_new_canvas_course(self):
        """Click on the canvas link which opens up in a new window. Switch to
        new window and parent frame
        """

        canvas_site_element = self.find_element(*Locators.SITE_FIELD)
        canvas_site_element.click()

        # switch to active window
        active_window = self._driver.window_handles[-1]
        self._driver.switch_to_window(active_window)

        # switch to parent frame
        self.focus_on_tool_frame()

