"""
This page models the main (landing) page of the Publish Courses Tool
"""

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.publish_courses.page_objects.base_page_object \
    import PublishCoursesBasePageObject


class Locators(object):
    pass


class MainPageObject(PublishCoursesBasePageObject):
    # page_loaded_locator = Locators.HEADING_ELEMENT

    # TODO: Select term fromd dropdown
    # TODO: Confirmation text after add


