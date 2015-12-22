from selenium.webdriver.common.by import Byfrom selenium_common.base_page_object import BasePageObjectfrom selenium.common.exceptions import NoSuchElementExceptionclass DashboardPageLocators(object):    PAGE_TITLE = (By.CSS_SELECTOR, 'h1')    PAGE_TITLE_TEXT = 'User Dashboard'class DashboardPageObject(BasePageObject):    def is_loaded(self):        self.focus_on_tool_frame()        title = None        try:            title = self.find_element(*DashboardPageLocators.PAGE_TITLE)        except NoSuchElementException:            return False        if title and DashboardPageLocators.PAGE_TITLE_TEXT  in self.get_title():            return True        else:            raise RuntimeError(                'Could not determine if Emailer main page loaded as expected;'                'title element was found but did not contain expected text'            )