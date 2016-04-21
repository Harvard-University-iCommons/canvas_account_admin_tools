from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.cross_listing.page_objects.cross_listing_base_page_object\
    import CrossListingBasePageObject


class Locators(object):
    HEADING_ELEMENT = (By.XPATH, 'h3')

class IndexPagePageObject(CrossListingBasePageObject):
    page_loaded_locator = Locators.HEADING_ELEMENT

    def find_heading_title(self):
        h3_element = self._driver.find_element(*Locators.HEADING_ELEMENT)
        print h3_element

