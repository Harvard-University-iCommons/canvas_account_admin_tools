"""
This page models the main (landing) page of the Cross Listing Tool
"""

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from selenium_tests.cross_listing.page_objects.cross_listing_base_page_object\
    import CrossListingBasePageObject


class Locators(object):
    CONFIRMATION_ALERT = (By.ID, 'result-message')
    DELETE_MODAL_CONFIRM = (By.ID, 'removeXlistMapModalConfirm')
    DATA_TABLE = (By.ID, 'DataTables_Table_0_wrapper')
    HEADING_ELEMENT = (By.XPATH, '//h3[contains(.,"Cross Listing")]')
    PRIMARY_CID_ADD_FIELD = (By.ID, 'primary-course')
    SEARCH_FIELD = (By.ID, 'search-query-string')
    SEARCH_BUTTON = (By.ID, 'search-submit-button')
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

    # todo: consider moving into the BasePageObject, with override flexibility
    def __init__(self, driver):
        super(MainPageObject, self).__init__(driver)
        self.wait = WebDriverWait(driver, 60)

    def add_cross_listing_pairing(self, primary_cid, secondary_cid):
        """Add two cross listed ID to be paired in cross-listing tool
        and confirms that an alert box returns after add.
        """

        if not self.form_input_available():
            return False

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
            self.wait.until(lambda s: s.find_element(
                *Locators.CONFIRMATION_ALERT).is_displayed())
        except TimeoutException:
            return False
        return True

    def delete_cross_listing_pairing(self, data_xlist_map_id):
        """ Deletes cross-listing pairing through crosslisting tool in
        admin console and confirms delete in modal window"""
        self.focus_on_tool_frame()
        self.find_element(*Locators.DELETE_CROSSLIST_ICON(
                data_xlist_map_id)).click()
        self.find_element(*Locators.DELETE_MODAL_CONFIRM).click()

    def confirmation_contains_text(self, expected_text):
        """
        Check that the expected text appears in the confirmation text box
        """
        try:
            self.wait.until(lambda s: s.find_element(
                *Locators.CONFIRMATION_ALERT).is_displayed())
            self.find_element(*Locators.ERROR_TEXT_LOCATOR(expected_text))
        except NoSuchElementException:
            return False
        else:
            return True

    def form_input_available(self):
        """
        if datatable is still loading, the primary, secondary, and search form
        fields are disabled; wait until they are available for user input
        """
        try:
            self.wait.until(EC.element_to_be_clickable(
                Locators.PRIMARY_CID_ADD_FIELD))
        except TimeoutException:
            return False  # forms were never clickable after a long wait
        return True  # forms are now available

    def get_confirmation_text(self):
        """
        Returns the confirmation text after add
        """
        alert = self.find_element(*Locators.CONFIRMATION_ALERT)
        confirmation_text = alert.text.strip()
        return confirmation_text

    def search(self, query_text):
        """
        Uses the search box to find a specific (set of) cross-listing map(s)
        :param query_text: string to search for using cross-listing search form
        :return: True if search was successful, False if error or datatable
                 never reloaded
        """

        if not self.form_input_available():
            return False

        self.find_element(*Locators.SEARCH_FIELD).send_keys(query_text)
        self.find_element(*Locators.SEARCH_BUTTON).click()

        return self.form_input_available()  # True once datatable reloads
