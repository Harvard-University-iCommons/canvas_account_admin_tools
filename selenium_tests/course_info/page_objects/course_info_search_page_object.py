
from selenium.webdriver.common.by import By
from selenium_tests.course_info.page_objects.course_info_base_page_object import CourseInfoBasePageObject


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

