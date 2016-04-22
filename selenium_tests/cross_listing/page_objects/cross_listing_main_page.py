"""
This page models the main (landing) page of the Cross Listing Tool
"""

from selenium.webdriver.common.by import By

from selenium_tests.cross_listing.page_objects.cross_listing_base_page_object\
    import CrossListingBasePageObject


class Locators(object):
    HEADING_ELEMENT = (By.XPATH, '//h3[contains(.,"Cross Listing")]')


class MainPageObject(CrossListingBasePageObject):
    page_loaded_locator = Locators.HEADING_ELEMENT
