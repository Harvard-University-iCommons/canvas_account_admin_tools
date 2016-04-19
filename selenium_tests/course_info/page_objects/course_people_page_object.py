from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.course_info.page_objects.course_info_base_page_object \
    import Locators as CourseInfoBasePageObjectLocators
from selenium_tests.course_info.page_objects.course_info_base_page_object \
    import CourseInfoBasePageObject


class Locators(object):

    ADD_PEOPLE_BUTTON = (By.XPATH, '//button[contains(.,"Add People")]')
    ADD_PEOPLE_SEARCH_TXT = (By.ID, 'emailHUID')
    ADD_TO_COURSE_BUTTON = (By.ID, 'add-user-btn-id')
    ALERT_SUCCESS_ALERT_BOX = (By.ID, 'alert-success')
    ALERT_SUCCESS_DELETE_PERSON = (By.XPATH, '//p[contains(.,"just removed")]')
    # todo: this can be simplified by applying proper IDs to the elements
    ADD_PEOPLE_CONFIRM_MODAL = (
        By.XPATH, '//h3[contains(.,"Confirm add people") and @class="modal-title"]')
    ADD_PEOPLE_CONFIRM_MODAL_CONFIRM_BUTTON = (
        By.XPATH, '//button[contains(.,"Add People") and @id="modalConfirm"]')
    DELETE_USER_CONFIRM = (By.XPATH, '//button[contains(.,"Yes, Remove User")]')
    PROGRESS_BAR = (By.ID, 'progressBarOuterWrapper')
    ROLES_DROPDOWN_LIST = (By.ID, "select-role-btn-id")

    @classmethod
    def DELETE_USER_ICON (cls, sis_user_id):
        """ returns a locator for the delete person link for sis_user_id """
        return By.CSS_SELECTOR, "a[data-sisID='{}']".format(sis_user_id)


class CoursePeoplePageObject(CourseInfoBasePageObject):
    page_loaded_locator = Locators.ADD_PEOPLE_BUTTON

    def is_person_on_page(self, lookup_text):
        """ looks up a person on in the people list by name or user id """
        element = self.get_cell_with_text(lookup_text)
        if element is not None:
            return True
        return False

    def is_person_removed_from_list(self, lookup_text):
        """
        verifies that a person is absent from the people list by name or
        user id
        """
        try:
            WebDriverWait(self._driver, 60).until_not(lambda s: s.find_element(
                *CourseInfoBasePageObjectLocators.TD_TEXT_XPATH(lookup_text)
                ).is_displayed())
        except TimeoutException:
            return False
        return True

    def search_and_add_users(self, search_terms, canvas_role):
        # Click "Add People" button to open the dialog
        self.find_element(*Locators.ADD_PEOPLE_BUTTON).click()
        # Clear Textbox
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_TXT).clear()
        # Enter user to search on
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_TXT).send_keys(
            search_terms)
        # Select role
        self.select_role_type(canvas_role)

        # Click 'Add to course' course button
        self.find_element(*Locators.ADD_TO_COURSE_BUTTON).click()

        # Confirm by clicking 'Add People' in modal
        WebDriverWait(self._driver, 30).until(lambda s: s.find_element(
            *Locators.ADD_PEOPLE_CONFIRM_MODAL).is_displayed())
        self.find_element(
            *Locators.ADD_PEOPLE_CONFIRM_MODAL_CONFIRM_BUTTON).click()

        # Don't return to test case until modal closes and progress bar starts
        # NOTE: In the event of a super-fast resolution of the add attempt, the
        # progress bar might not be displayed long enough for Selenium to pick
        # it up; we may wish to do an alternate test (for success/error
        # messages) if this first one fails.

        WebDriverWait(self._driver, 30).until_not(lambda s: s.find_element(
            *Locators.PROGRESS_BAR).is_displayed())

    def select_role_type(self, canvas_role):
        """ select a role from the roles dropdown """
        self.find_element(*Locators.ROLES_DROPDOWN_LIST).click()
        self.find_element(By.LINK_TEXT, canvas_role).click()

    def people_added(self, expected_successes, expected_failures):
        """
        Checks to see if the number of people successfully added to course
        and number of people not added to course matches expected numbers
        """
        element = None

        success_message = 'No people were added to the course.'
        if expected_successes == 1:
            success_message = '1 person was added to the course.'
        elif expected_successes > 1:
            success_message = '{} people were added to the course.'.format(
                expected_successes)

        failure_message = ''
        if expected_failures == 1:
            failure_message = '1 person could not be added.'
        elif expected_failures > 1:
            failure_message = '{} people could not be added.'.format(
                    expected_failures)
        '{} {}'.format(success_message, failure_message).strip()
        try:
            element = self.find_element(*Locators.ALERT_SUCCESS_ALERT_BOX)
        except NoSuchElementException:
            return False
        return element.text == '{} {}'.format(
            success_message, failure_message).strip()

    def delete_was_successful(self):
        # Verify delete text
        # todo: this does not check _which_ delete was successful...
        try:
            self.find_element(*Locators.ALERT_SUCCESS_DELETE_PERSON)
        except NoSuchElementException:
            return False
        return True

    def delete_user(self, user_id):
        """ Deletes user from a course through the admin console and confirms
        delete in modal window """
        self.find_element(*Locators.DELETE_USER_ICON(user_id)).click()
        self.find_element(*Locators.DELETE_USER_CONFIRM).click()

