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
    DELETE_MODAL_CONFIRM = (By.ID, 'removeXlistMapModalConfirm')
    DATA_TABLE = (By.ID, 'DataTables_Table_0_wrapper')
    HEADING_ELEMENT = (By.XPATH, '//h3[contains(.,"Cross Listing")]')
    PRIMARY_CID_ADD_FIELD = (By.ID, 'primary-course')
    SECONDARY_CID_ADD_FIELD = (By.ID, 'secondary-course')
    SUBMIT_BUTTON = (By.ID, 'submit-new-cross-listing-btn')

    @classmethod
    def DELETE_CROSSLIST_ICON(cls, data_xlist_map_id):
        """ returns a locator for the xlist link for the xlist_map_id"""
        return By.CSS_SELECTOR, "a[data-xlist-map-id='{}']".format(
                data_xlist_map_id)

    @classmethod
    def ERROR_TEXT_LOCATOR(cls, expected_text):
        """ returns a locator for expected error text"""
        return By.XPATH, ".//div[contains(.,'{}') and " \
                         "@id='result-message']".format(expected_text)


class MainPageObject(CrossListingBasePageObject):
    page_loaded_locator = Locators.HEADING_ELEMENT

    def add_cross_listing_pairing(self, primary_cid, secondary_cid):
        """Add two cross listed ID to be paired in cross-listing tool
        and confirms that an alert box returns after add.
        """

        # Fills in the primary CID for cross-listing
        primary_cid_field = self.find_element(*Locators.PRIMARY_CID_ADD_FIELD)
        primary_cid_field.send_keys(primary_cid)

        # Fills in the secondary CID field for cross-listing
        secondary_cid_field = self.find_element(
                *Locators.SECONDARY_CID_ADD_FIELD)
        secondary_cid_field.send_keys(secondary_cid)

        # Clicks on submit button to pair the cross listing
        self.find_element(*Locators.SUBMIT_BUTTON).click()

        try:
            WebDriverWait(self._driver, 60).until(lambda s: s.find_element(
                *Locators.CONFIRMATION_ALERT).is_displayed())
        except TimeoutException:
            return False
        return True

    def delete_cross_listing_pairing(self, data_xlist_map_id):
        """ Deletes cross-listing pairing through crosslisting tool in
        admin console and confirms delete in modal window"""
        self.find_element(*Locators.DELETE_CROSSLIST_ICON(
                data_xlist_map_id)).click()
        self.find_element(*Locators.DELETE_MODAL_CONFIRM).click()

    def is_locator_text_present(self, expected_text):
        """
        Check to that locator text appears on the confirmation page
        """
        try:
            self.find_element(*Locators.ERROR_TEXT_LOCATOR(expected_text))
        except NoSuchElementException:
            return False
        else:
            return True
