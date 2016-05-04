"""
This page models the main (landing) page of the Cross Listing Tool
"""

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.cross_listing.page_objects.cross_listing_base_page_object\
    import CrossListingBasePageObject


class Locators(object):
    CONFIRMATION_ALERT = (By.ID, 'result-message')
    ERROR_MESSAGE_1 = (By.XPATH, './/div[contains(.,"already exists")]')
    ERROR_MESSAGE_2 = (By.XPATH, './/div[contains(.,"already crosslisted")]')
    ERROR_MESSAGE_3 = (By.XPATH, './/div[contains(.,"currently crosslisted")]')
    ERROR_MESSAGE_4 = (By.XPATH, './/div[contains(.,"not be crosslisted")]')
    ERROR_MESSAGE_5 = (By.XPATH, './/div[contains(.,"backend")]')
    HEADING_ELEMENT = (By.XPATH, '//h3[contains(.,"Cross Listing")]')
    PRIMARY_CID_ADD_FIELD = (By.ID, 'primary-course')
    SECONDARY_CID_ADD_FIELD = (By.ID, 'secondary-course')
    SUBMIT_BUTTON = (By.ID, 'submit-new-cross-listing-btn')


class MainPageObject(CrossListingBasePageObject):
    page_loaded_locator = Locators.HEADING_ELEMENT

    def add_cross_listing_pairing(self, primary_cid, secondary_cid):
        """Add two cross listed ID to be paired in cross-listing tool"""

        # Fills in the primary CID for cross-listing
        primary_cid_field = self.find_element(*Locators.PRIMARY_CID_ADD_FIELD)
        primary_cid_field.send_keys(primary_cid)

        # Fills in the secondary CID field for cross-listing
        secondary_cid_field = self.find_element(
                *Locators.SECONDARY_CID_ADD_FIELD)
        secondary_cid_field.send_keys(secondary_cid)

        # Clicks on submit button to pair the cross listing
        self.find_element(*Locators.SUBMIT_BUTTON).click()

    def confirm_presence_of_confirmation_alert(self):
        """
        :param self:
        :return: Confirms that an alert box returns after add
        """
        try:
            WebDriverWait(self._driver, 60).until(lambda s: s.find_element(
                    *Locators.CONFIRMATION_ALERT).is_displayed())
        except TimeoutException:
            return False
        return True

    def get_confirmation_text(self):
        """
        Returns the confirmation text after add
        """
        alert = self.find_element(*Locators.CONFIRMATION_ALERT)
        confirmation_text = alert.text.strip()
        return confirmation_text

    def verify_error_elements_are_present(self):
        """
        There are several possible error messages.  This verifies that one of
        the several possible errors appear for unsuccessful add
        """
        count = 0
        try:
            print self.get_confirmation_text()
            if self.find_element(*Locators.ERROR_MESSAGE_1).is_displayed():
                # increments counter by 1 if message is found
                count += 1
        except NoSuchElementException:
            pass

        try:
            if self.find_element(*Locators.ERROR_MESSAGE_2).is_displayed():
                count += 1
        except NoSuchElementException:
            pass

        try:
            if self.find_element(*Locators.ERROR_MESSAGE_3).is_displayed():
                count += 1
        except NoSuchElementException:
            pass

        try:
            if self.find_element(*Locators.ERROR_MESSAGE_4).is_displayed():
                count += 1
        except NoSuchElementException:
            pass

        try:
            if self.find_element(*Locators.ERROR_MESSAGE_5).is_displayed():
                count += 1
        except NoSuchElementException:
            pass

        # A count equal of 1 or more indicates one of error messages appear.
        if count > 0:
            return True
        return False
