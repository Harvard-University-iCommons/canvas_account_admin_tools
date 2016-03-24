from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.course_info.page_objects.course_info_base_page_object \
    import CourseInfoBasePageObject
from selenium_tests.course_info.page_objects.course_people_page_object \
    import Locators as CoursePeoplePageLocators


class Locators(object):
    COURSE_RESULTS_TABLE = (By.ID, "courseInfoDT")
    COURSE_SEARCH_TEXTBOX = (By.XPATH, "//input[@type='text']")
    SEARCH_BUTTON = (By.XPATH, '//button[contains(.,"Search")]')
    SELECT_COURSE_TYPE_DROPDOWN = (By.ID, "dropdownMenuSites")
    SELECT_SCHOOL_DROPDOWN = (By.ID, "dropdownMenuSchools")
    SELECT_TERM_DROPDOWN = (By.ID, "dropdownMenuTerm")
    SELECT_YEAR_DROPDOWN = (By.ID, "dropdownMenuYear")

    @classmethod
    def COURSE_LINK_HREF_CSS(cls, cid):
        """ returns a locator for a course detail link in the course table """
        return By.CSS_SELECTOR, 'a[href="#/details/{}"]'.format(cid)


class CourseSearchPageObject(CourseInfoBasePageObject):
    page_loaded_locator = Locators.COURSE_RESULTS_TABLE

    def is_course_displayed(self, cid=None, title=None):
        # todo: this could be refactored along with select_course()
        self.focus_on_tool_frame()
        try:
            if cid:
                self.find_element(*Locators.COURSE_LINK_HREF_CSS(cid))
            elif title:
                self.find_element((By.LINK_TEXT, title))
            else:
                raise RuntimeError('select_course() requires cid or title')
        except NoSuchElementException:
            return False
        return True

    def select_school(self, school):
        """ select a school from the schools dropdown """
        self.find_element(*Locators.SELECT_SCHOOL_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, school).click()

    def select_year(self, year):
        """ select a year from the year dropdown """
        self.find_element(*Locators.SELECT_YEAR_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, year).click()

    def select_term(self, term):
        """ select a term from the term dropdown """
        self.find_element(*Locators.SELECT_TERM_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, term).click()

    def select_course_type(self, type):
        """ select a site type from the type dropdown """
        self.find_element(*Locators.SELECT_COURSE_TYPE_DROPDOWN).click()
        self.find_element(By.LINK_TEXT, type).click()

    def submit_search(self, search_text):
        self.focus_on_tool_frame()
        search_textbox = self.find_element(*Locators.COURSE_SEARCH_TEXTBOX)
        search_textbox.clear()
        search_textbox.send_keys(search_text)
        self.find_element(*Locators.SEARCH_BUTTON).click()
        # loading the results can take a long time, so explicitly wait longer
        WebDriverWait(self._driver, 30).until(lambda s: s.find_element(
            *Locators.COURSE_RESULTS_TABLE).is_displayed())

    def select_course(self, cid=None, title=None):
        self.focus_on_tool_frame()
        if cid:
            self.find_element(*Locators.COURSE_LINK_HREF_CSS(cid)).click()
        elif title:
            self.find_element((By.LINK_TEXT, title)).click()
        else:
            raise RuntimeError('select_course() requires cid or title')
        # loading the results can take a long time, so explicitly wait longer
        WebDriverWait(self._driver, 30).until(lambda s: s.find_element(
            *CoursePeoplePageLocators.ADD_PEOPLE_BUTTON).is_displayed())

    def get_td_text(self, course_code_text):
        """
        :return: The text in the web element in the course code column
                 else return None
        """
        element = self.find_element(
            *self.TD_TEXT_XPATH(course_code_text))

        if element.text > 0:
            return element.text
        else:
            return None
