"""
This page models the main (landing) page of the Publish Courses Tool
"""
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


from selenium_tests.publish_courses.page_objects.base_page_object \
    import PublishCoursesBasePageObject


class Locators(object):
    PUBLISH_ALL_BUTTON = (By.ID, "publishAllButton")
    TERM_DROPDOWN = (By.ID, "dropdownMenuTerm")
    RESULT_CONFIRMATION = (By.ID, "result-message")

    @classmethod
    def FIND_LINK_WITH_TEXT(cls, text_value):
        """Locates the xpath, given the text value"""
        return By.XPATH, "//a[contains(.,'{}')]".format(text_value)


class MainPageObject(PublishCoursesBasePageObject):
    page_loaded_locator = Locators.PUBLISH_ALL_BUTTON

    def is_publish_all_button_enabled(self):
        """Check to see if "Publish All" button is enabled"""
        publish_all_button = self.find_element(*Locators.PUBLISH_ALL_BUTTON)
        return (publish_all_button.is_enabled() and
                publish_all_button.text == 'Publish All')

    def publish_courses(self):
        publish_courses = self.find_element(*Locators.PUBLISH_ALL_BUTTON)
        publish_courses.click()

    def result_message_visible(self):
        """
        Verify that the result message apepears after clicking on Publish All
        """
        try:
            WebDriverWait(self._driver, 30).until(
                EC.visibility_of_element_located(Locators.RESULT_CONFIRMATION))
        except TimeoutException:
            return False
        return True

    def select_term(self, term):
        """Select a term from the dropdown. Note that the term dropdown is
        not of the type "dropdown" but a "button" type, so the selenium select
        option is not used to select a term in this instance.  Instead,
        we are looking for the a href element that matches the term name here"""

        WebDriverWait(self._driver, 30).until(EC.visibility_of_element_located(
                    Locators.TERM_DROPDOWN))
        self.find_element(*Locators.TERM_DROPDOWN).click()
        term_selection = self.find_element(*Locators.FIND_LINK_WITH_TEXT(
            term))
        term_selection.click()


