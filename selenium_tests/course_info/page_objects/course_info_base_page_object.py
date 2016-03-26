from selenium.webdriver.common.by import By

from selenium_common.base_page_object import BasePageObject


class CourseInfoBasePageObject(BasePageObject):
    def __init__(self, driver):
        super(CourseInfoBasePageObject, self).__init__(driver)
        self.focus_on_tool_frame()

    @classmethod
    def TD_TEXT_XPATH(cls, search_text):
        """ returns a locator for a table cell element in the people table;
        search_text should be user's name, user_id, etc
        Note:
        This should match exact text, which is better than contains(),
        but it does depend on your use case
         -- presumably the other tests that are making use of this PO
            will still work (that is, their use case is also to search
            for an exact match).
         """
        return By.XPATH, "//td[.='{}']".format(search_text)
