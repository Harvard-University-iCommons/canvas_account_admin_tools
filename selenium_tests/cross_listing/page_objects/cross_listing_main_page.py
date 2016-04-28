"""
This page models the main (landing) page of the Cross Listing Tool
"""
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from selenium_tests.cross_listing.page_objects.cross_listing_base_page_object\
    import CrossListingBasePageObject


class Locators(object):
    # TODO STUBS -- TO BE CLEANED UP ONCE ACTUAL LOCATORS ARE AVAIALBLE:
    ADD_CROSS_LISTING_BUTTON = (By.ID, "SOME_SUBMIT_BUTTON")
    CONFIRMATION_ALERT = (By.ID, 'SOME_ALERT_BOX')
    HEADING_ELEMENT = (By.XPATH, '//h3[contains(.,"Cross Listing")]')
    PRIMARY_CID_ADD_FIELD = (By.ID, 'PRIMARY_ELEMENT')
    SECONDARY_CID_ADD_FIELD = (By.ID, 'SECONDARY_ELEMENT')


class MainPageObject(CrossListingBasePageObject):
    page_loaded_locator = Locators.HEADING_ELEMENT

    #TODO: This is a stub
    def add_cross_listing_pairing(self, primary_cid, secondary_cid):
        """Add two cross listed ID to be paired in cross-listing tool"""

        # Fill in the primary CID for cross-listing
        primary_cid_field = self.find_element(*Locators.PRIMARY_CID_ADD_FIELD)
        primary_cid_field.send_keys(primary_cid)

        # Fill in the secondary CID field for cross-listing
        secondary_cid_field = self.find_element(*Locators.SECONDARY_CID_ADD_FIELD)
        secondary_cid_field.send_keys(secondary_cid)

        # Click on submit button to pair the cross listing
        self.find_element(*Locators.ADD_CROSS_LISTING_BUTTON)

    #TODO:  This is a stub only
    def confirm_presence_of_confirmation_alert(self):
        """
        :param self:
        :return: Confirms that an alert box returns after add
        """
        try:
            self.find_element(*Locators.CONFIRMATION_ALERT)
        except NoSuchElementException:
            return False

    # TODO:  This is a stub only.  May not need if if checking by text
    def is_add_successful(self, primary_cid, secondary_cid):
        """This confirms successful add by checking on presence
        of the primary_cid in the table"""

        ci_search = CrossListingBasePageObject(self.driver)
        check_primary = ci_search.get_cell_with_text(primary_cid)
        check_secondary = ci_search.get_cell_with_text(secondary_cid)

        # If check_primary or check_secondary returns NONE, the ids are not on
        # the page which indicates an unsuccessful add.

        if check_primary == "None" or check_secondary == "None":
            return False
        else:
            return True

    def get_confirmation_text(self):
        """
        Returns either the success or failure confirmation text
        """
        alert = self.find_element(*Locators.CONFIRMATION_ALERT)
        confirmation_text = alert.text
        return confirmation_text.strip()
