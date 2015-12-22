from selenium.webdriver.common.by import By
from selenium_common.base_page_object import BasePageObject
from selenium.common.exceptions import NoSuchElementException

TITLE_TEXT = 'COMPSCI 189r'

class CourseShoppingLocators(object):
    COURSE_TITLE = (By.ID, 'section-tabs-header')
    ADD_COURSE_LINK = (By.LINK_TEXT, "Add Course")


class CourseShoppingPageObject(BasePageObject):

    def is_loaded(self):
        try:
            self.find_element(*CourseShoppingLocators.COURSE_TITLE)
        except NoSuchElementException:
            return False
        return True

    def is_shopping_available(self):
        try:
            webelement = self.find_element(*CourseShoppingLocators.ADD_COURSE_LINK)
        except NoSuchElementException:
            return False
        return webelement.is_displayed()

