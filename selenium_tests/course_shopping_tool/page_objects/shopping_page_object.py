from selenium.webdriver.common.by import By
from selenium_common.base_page_object import BasePageObject
from selenium.common.exceptions import NoSuchElementException,TimeoutException


class CourseShoppingLocators(object):
    COURSE_TITLE = (By.ID, 'section-tabs-header')
    COURSE_BANNER = (By.ID, 'course-shopping')


class CourseShoppingPageObject(BasePageObject):

    def is_loaded(self):
        try:
            self.find_element(*CourseShoppingLocators.COURSE_TITLE)
        except NoSuchElementException:
            return False
        return True

    def is_shopping_available(self):
        try:
            self.find_element(*CourseShoppingLocators.COURSE_BANNER)
        except NoSuchElementException:
            return False
        return True
