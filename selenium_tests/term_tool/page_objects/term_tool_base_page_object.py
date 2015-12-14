from selenium.common.exceptions import NoSuchElementException
from selenium_common.base_page_object import BasePageObject

# This is the base class that all page models can inherit from


class TermToolBasePageObject(BasePageObject):

    def __init__(self, driver):
        super(TermToolBasePageObject, self).__init__(driver)
        try:
            self._driver.switch_to.frame(self._driver.find_element_by_id("tool_content"))
        except NoSuchElementException:
            pass

    def open(self, url):
        self._driver.get(url)
        return self
