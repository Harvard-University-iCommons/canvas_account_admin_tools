from selenium.webdriver.common.by import By

from selenium_common.base_page_object import BasePageObject


class Locators(object):
    COURSE_TITLE = (By.ID, 'section-tabs-header')


class CourseShoppingPageObject(BasePageObject):

    def is_loaded(self):
        title = self.find_element(*Locators.COURSE_TITLE)
        return title.text == 'COMPSCI 189r'
