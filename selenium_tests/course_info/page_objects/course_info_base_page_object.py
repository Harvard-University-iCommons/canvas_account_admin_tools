from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_common.base_page_object import BasePageObject


class Locators(object):
    @classmethod
    def TD_TEXT_XPATH(cls, search_text):
        """
        Returns a locator for the first table cell element in any table on the
        page whose text matches `search_text`. Note: matches text of element
        (not inclusive of child-elements) with leading and trailing space
        stripped and whitespace normalized between words.
        """
        return By.XPATH, "//td[normalize-space(text())='{}']".format(
            search_text)


class CourseInfoBasePageObject(BasePageObject):
    def __init__(self, driver):
        super(CourseInfoBasePageObject, self).__init__(driver)
        self.focus_on_tool_frame()

    def get_cell_with_text(self, search_text):
        """
        :return: The text in the web element in the course code column
                 else return None
        """

        try:
            return self.find_element(*Locators.TD_TEXT_XPATH(search_text))
        except NoSuchElementException:
            return None
