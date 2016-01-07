from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_common.base_page_object import BasePageObject


class Locators(object):
    TITLE = (By.CSS_SELECTOR, 'a.navbar-brand')


class ShoppingExcludePageObject(BasePageObject):

    def is_loaded(self):
        title = self.find_element(*Locators.TITLE)
        return title.text == 'Term Tool'
