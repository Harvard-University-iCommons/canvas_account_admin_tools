from selenium.webdriver.common.by import By
from selenium_tests.course_info.page_objects.course_info_base_page_object import CourseInfoBasePageObject
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

class CourseSearchPageLocators(object):
    # List of WebElements found on course search page
    PAGE_TITLE = (By.CSS_SELECTOR, "h1")
    PAGE_TITLE_TEXT = "Find Course"
    COURSE_INFO_SEARCH_BUTTON = (By.CLASS_NAME, "button")
    COURSE_INSTANCE_TABLE = (By.ID, "courseInstanceDT")
    SELECT_SCHOOL_DROPDOWN = (By.ID, "dropdownMenuSchools")
    SELECT_TERM_DROPDOWN = (By.ID, "dropdownMenuTerm")
    SELECT_YEAR_DROPDOWN = (By.ID, "dropdownMenuYear")
    SELECT_COURSE_TYPE_DROPDOWN = (By.ID, "dropdownMenuSites")
    # The Search button is the 5th button on the page(all the dropdowns are also rendered as buttons)
    COURSE_INFO_SEARCH_BUTTON_PATH = (By.XPATH, '(//button[@type="button"])[5]')
    COURSE_RESULTS_TABLE = (By.ID, "courseInfoDT")
    COURSE_SEARCH_TEXTBOX = (By.XPATH, "//input[@type='text']")
    COURSE_LINK_TEXT = "Latin Paleography and Manuscript Culture: Seminar"
    COURSE_ID_LINK = (By.LINK_TEXT, COURSE_LINK_TEXT)
    TEST_PERSON_ON_PAGE = (By.XPATH, "//td[contains(text(), '20299916')]")
    ADD_PEOPLE_SEARCH_BUTTON = (By.ID, "BTN_Add_People_Search")
    ADD_PEOPLE_SEARCH_TXT = (By.ID, "emailHUID")
    ROLES_DROPDOWN_LIST = (By.ID, "LIST_Roles")
    ADD_TO_COURSE_BUTTON = (By.ID, "BTN_Add_People_Course")
    PEOPLE_TABLE = (By.ID, "TBL_people")
    PEOPLE_ROWS = (By.TAG_NAME, "tr")


class CourseSearchPageObject(CourseInfoBasePageObject):

    def is_loaded(self):
        """ determine if the page loaded by validating teh page title page """
        # frame context stickiness is a bit flaky for some reason; make sure we're in the tool_content frame context
        # before checking for elements on the expected
        self.focus_on_tool_frame()
        page_title_element = self.get_page_title()
        if page_title_element and page_title_element.text == CourseSearchPageLocators.PAGE_TITLE_TEXT:
            return True
        else:
            return False

    def get_page_title(self):
        element = self.find_element(*CourseSearchPageLocators.PAGE_TITLE)
        return element

    def select_school(self, school):
        """ select a school from the schools dropdown """
        self.find_element(*CourseSearchPageLocators.SELECT_SCHOOL_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, school).click()

    def select_year(self, year):
        """ select a year from the year dropdown """
        self.find_element(*CourseSearchPageLocators.SELECT_YEAR_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, year).click()

    def select_term(self, term):
        """ select a term from the term dropdown """
        self.find_element(*CourseSearchPageLocators.SELECT_TERM_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, term).click()

    def select_course_type(self, type):
        """ select a site type  from the  type dropdown """
        self.find_element(*CourseSearchPageLocators.SELECT_COURSE_TYPE_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, type).click()

    def submit_search(self, search_text):
        self.focus_on_tool_frame()
        self.find_element(*CourseSearchPageLocators.SELECT_SCHOOL_DROPDOWN).click()
        self.find_element(*CourseSearchPageLocators.COURSE_SEARCH_TEXTBOX).clear()
        self.find_element(*CourseSearchPageLocators.COURSE_SEARCH_TEXTBOX).send_keys(search_text)
        self.find_element(*CourseSearchPageLocators.COURSE_INFO_SEARCH_BUTTON_PATH).click()

    def select_course_id(self):
        self.focus_on_tool_frame()
        self.find_element(*CourseSearchPageLocators.COURSE_ID_LINK).click()

    def select_a_course_on_page(self):
        self.focus_on_tool_frame()
        self.select_course_id()

    def find_test_person_on_page(self):
        element = self.find_element(*CourseSearchPageLocators.TEST_PERSON_ON_PAGE)
        return element

    def search_for_a_user(self, user_id):
        # Click "Add People" button
        self.find_element(*CourseSearchPageLocators.ADD_PEOPLE_SEARCH_BUTTON).click()
        # Clear Textbox
        self.find_element(*CourseSearchPageLocators.ADD_PEOPLE_SEARCH_TXT).clear()
        # Enter user to search on
        self.find_element(*CourseSearchPageLocators.ADD_PEOPLE_SEARCH_TXT).send_keys(user_id)

    def add_user_to_course(self, user_id, role):
        # Click "Add People" button
        self.search_for_a_user(user_id)
        # Select role
        select_role = self.select_role(role, user_id)
        #  Add user to course
        if select_role:
            self.find_element(*CourseSearchPageLocators.ADD_TO_COURSE_BUTTON).click()
        else:
            return False


    def select_role(self, role_visible_text=None, user_id=None):
        """ Select role for user, return true if visible, else return false """

        # Get the role dropdown as instance of Select class
        if user_id:
            user_role_select = self._driver.find_element_by_css_selector('[data-selenium-user-id=%s]' % user_id)
        else:
            try:
                user_role_select = self.find_element(*CourseSearchPageLocators.ROLES_DROPDOWN_LIST)
            except NoSuchElementException:
                try:
                    self.focus_on_tool_frame()
                    user_role_select = self.find_element(*CourseSearchPageLocators.ROLES_DROPDOWN_LIST)
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
        user_table_id = self.find_element(*CourseSearchPageLocators.PEOPLE_TABLE)
        rows = user_table_id.find_elements(*CourseSearchPageLocators.PEOPLE_ROWS)
        match_found = False

        for row in rows:
            row_user = row.find_element(By.TAG_NAME, "td")[2]  # find univ_id to match on
            if row_user == user_id:   # break, if match is found
                match_found = True
                break

        if not match_found:
            return False

