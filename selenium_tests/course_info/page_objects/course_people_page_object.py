from selenium.webdriver.common.by import By
from selenium_tests.course_info.page_objects.course_info_base_page_object import CourseInfoBasePageObject
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC


class Locators(object):
    ADD_PEOPLE_BUTTON = (By.XPATH, '//button[contains(.,"Add People")]')
    ADD_PEOPLE_SEARCH_BUTTON = (By.ID, "addPeopleBtn")
    ADD_PEOPLE_SEARCH_TXT = (By.ID, "emailHUID")
    ADD_TO_COURSE_BUTTON = (By.ID, "add-user-btn-id")
    ALERT_SUCCESS_PERSON = (By.XPATH, '//p[contains(.,"just added")]')
    ROLES_DROPDOWN_LIST = (By.ID, "select-role-btn-id")

    @classmethod
    def TD_TEXT_XPATH(cls, search_text):
        """ returns a locator for a table cell element in the people table;
        search_text should be user's name, user_id, etc """
        return By.XPATH, '//td[contains(text(), "{}")]'.format(search_text)


class CoursePeoplePageObject(CourseInfoBasePageObject):

    def is_loaded(self):
        """ page is loaded if add people button is present """
        # frame context stickiness is a bit flaky for some reason; make sure
        # we're in the tool_content frame context before checking for elements
        self.focus_on_tool_frame()
        try:
            self.find_element(*Locators.ADD_PEOPLE_BUTTON)
        except NoSuchElementException:
            return False
        return True

    def is_person_on_page(self, lookup_text):
        """ looks up a person on page by name or user id """
        try:
            self.find_element(*Locators.TD_TEXT_XPATH(lookup_text))
        except NoSuchElementException:
            return False
        return True

    def search_and_add_user(self, user_id, role):
        # Click "Add People" button to open the dialog
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_BUTTON).click()
        # Clear Textbox
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_TXT).clear()
        # Enter user to search on
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_TXT).send_keys(user_id)
        # Select role
        self.select_role_type(role)

        # Click 'Add to course' course button
        try:
            self.find_element(*Locators.ADD_TO_COURSE_BUTTON).click()
            WebDriverWait(self._driver, 60).until\
                (EC.presence_of_element_located((By.ID, "success-alert")))

        except TimeoutException:
            return False

    def select_role_type(self, role):
        """ select a role from the roles dropdown """
        self.find_element(*Locators.ROLES_DROPDOWN_LIST).click()
        self.find_element(By.LINK_TEXT, role).click()

    def find_success_message(self):
        self.find_element(*Locators.ALERT_SUCCESS_PERSON)
