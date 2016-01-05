from selenium.webdriver.common.by import By
from selenium_tests.course_info.page_objects.course_info_base_page_object import CourseInfoBasePageObject
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException


class Locators(object):
    ADD_PEOPLE_BUTTON = (By.XPATH, '//button[contains(.,"Add People")]')
    TD_TEXT_XPATH = '//td[contains(text(), "{}")]'  # {} = name, user_id, etc.
    ADD_PEOPLE_SEARCH_BUTTON = (By.ID, "BTN_Add_People_Search")
    ADD_PEOPLE_SEARCH_TXT = (By.ID, "emailHUID")
    ROLES_DROPDOWN_LIST = (By.ID, "LIST_Roles")
    ADD_TO_COURSE_BUTTON = (By.ID, "BTN_Add_People_Course")
    PEOPLE_TABLE = (By.ID, "TBL_people")
    PEOPLE_ROWS = (By.TAG_NAME, "tr")


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
            self.find_element(
                *(By.XPATH, Locators.TD_TEXT_XPATH.format(lookup_text)))
        except NoSuchElementException:
            return False
        return True

    def search_for_a_user(self, user_id):
        # Click "Add People" button
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_BUTTON).click()
        # Clear Textbox
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_TXT).clear()
        # Enter user to search on
        self.find_element(*Locators.ADD_PEOPLE_SEARCH_TXT).send_keys(
            user_id)

    def add_user_to_course(self, user_id, role):
        # Click "Add People" button
        self.search_for_a_user(user_id)
        # Select role
        select_role = self.select_role(role, user_id)
        #  Add user to course
        if select_role:
            self.find_element(*Locators.ADD_TO_COURSE_BUTTON).click()
        else:
            return False

    def select_role(self, role_visible_text=None, user_id=None):
        """ Select role for user, return true if visible, else return false """

        # Get the role dropdown as instance of Select class
        if user_id:
            user_role_select = self._driver.find_element_by_css_selector(
                '[data-selenium-user-id=%s]' % user_id)
        else:
            try:
                user_role_select = self.find_element(
                    *Locators.ROLES_DROPDOWN_LIST)
            except NoSuchElementException:
                try:
                    self.focus_on_tool_frame()
                    user_role_select = self.find_element(
                        *Locators.ROLES_DROPDOWN_LIST)
                except:
                    return False

        selenium_select = Select(user_role_select)

        try:
            if role_visible_text:
                selenium_select.select_by_visible_text(role_visible_text)
            else:
                # Default to this value if no role is passed in
                selenium_select.select_by_index(1)
        except:
            return False

        return True

    def find_user_added_on_page(self, user_id):
        user_table_id = self.find_element(*Locators.PEOPLE_TABLE)
        rows = user_table_id.find_elements(*Locators.PEOPLE_ROWS)
        match_found = False

        for row in rows:
            row_user = row.find_element(By.TAG_NAME, "td")[
                2]  # find univ_id to match on
            if row_user == user_id:  # break, if match is found
                match_found = True
                break

        if not match_found:
            return False
