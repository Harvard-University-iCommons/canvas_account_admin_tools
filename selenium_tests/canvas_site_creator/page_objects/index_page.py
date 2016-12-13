from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_common.webelements import Select

from selenium_tests.canvas_site_creator.page_objects.base_page_object \
    import BulkCreateBasePageObject


class Locators(object):
    COURSE_GROUP_DROPDOWN = (By.ID, "courseGroupSelect")
    CREATE_CANVAS_SITES_BUTTON = (By.ID, "createSitesButton")
    DEPARTMENT_DROPDOWN = (By.ID, "departmentSelect")
    TERM_SELECT_DROPDOWN = (By.ID, "termSelect")
    UNAUTHORIZED_MESSAGE = (By.ID, "unauthorized_message")
    CREATE_NEW_COURSE_LINK = (By.ID, "createNewCourseButton")
    # This is locating a specific element on bulk create table (row 3/column 3)
    COURSE_CODE_LOCATOR_R3_C3 = (
        By.XPATH, ".//*[@id='courseInstanceDT']/tbody/tr[3]/td[3]")
    # This is locating a specific element on bulk create table (row 4/column 3)
    COURSE_CODE_LOCATOR_R4_C3 = (
        By.XPATH, ".//*[@id='courseInstanceDT']/tbody/tr[4]/td[3]")


class IndexPageObject(BulkCreateBasePageObject):
    """ The landing page of the bulk create tool """
    page_loaded_locator = Locators.TERM_SELECT_DROPDOWN


    def create_canvas_sites(self):
        WebDriverWait(self._driver, 30).until(
                EC.visibility_of_element_located(
                        Locators.CREATE_CANVAS_SITES_BUTTON)
            )
        self.find_element(*Locators.CREATE_CANVAS_SITES_BUTTON).click()

    def is_authorized(self):
        try:
            self.find_element(*Locators.UNAUTHORIZED_MESSAGE)
        except NoSuchElementException:
            # unauthorized message not found, we should be on landing page
            return self.is_loaded()
        # we found the unauthorized message, so we're explicitly unauthorized
        return False

    def select_course_group(self, course_group):
        select = Select(self.find_element(*Locators.COURSE_GROUP_DROPDOWN))
        select.select_by_visible_text(course_group)

    def select_department(self, department):
        select = Select(self.find_element(*Locators.DEPARTMENT_DROPDOWN))
        select.select_by_visible_text(department)

    def select_term(self, term):
        WebDriverWait(self._driver, 30).until(EC.visibility_of_element_located(
                Locators.TERM_SELECT_DROPDOWN))
        select = Select(self.find_element(*Locators.TERM_SELECT_DROPDOWN))
        select.select_by_visible_text(term)

    def get_new_course_link(self):
        """
        This function will locate and click onto the create a new course link
        """
        element = self.find_element(*Locators.CREATE_NEW_COURSE_LINK)
        element.click()
