from selenium.webdriver.common.by import Byfrom selenium_common.base_page_object import BasePageObjectclass IndexPageLocators(object):    PAGE_TITLE = (By.CSS_SELECTOR, 'h1')    PAGE_TITLE_TEXT = 'User Dashboard'class IndexPageObject(BasePageObject):    def is_loaded(self):        self.focus_on_tool_frame()        index_page_title = self.get_page_title()        if index_page_title and index_page_title.text ==\                IndexPageLocators.PAGE_TITLE:            return True        else:            return False    def get_page_title(self):        element = self.find_element(*IndexPageLocators.PAGE_TITLE)        return element