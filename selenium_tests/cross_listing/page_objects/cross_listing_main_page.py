"""
This page models the main (landing) page of the Cross Listing Tool
"""

from selenium.webdriver.common.by import By

from selenium_tests.cross_listing.page_objects.cross_listing_base_page_object\
    import CrossListingBasePageObject


class Locators(object):
    HEADING_ELEMENT = (By.XPATH, '//h3[contains(.,"Cross Listing")]')
    # TODO STUBS:
    ADD_ALERT_TEXT = (By.ID, 'SOME_ALERT_BOX')
    PRIMARY_INSTANCE_ADD_FIELD = (By.ID, 'PRIMARY_ELEMENT')
    SECONDARY_INSTANCE_ADD_FIELD = (By.ID, 'SECONDARY_ELEMENT')
    ADD_CROSS_LISTING_BUTTON = (By.ID, "SOME_SUBMIT_BUTTON")


class MainPageObject(CrossListingBasePageObject):
    page_loaded_locator = Locators.HEADING_ELEMENT

    #TODO: This is a stub
    def add_cross_listing_pairing(self, course_instance_1, course_instance_2):
        """Add two cross listed ID to be paired in cross-listing tool"""

        PRIMARY_COURSE_INSTANCE= self.find_element(*By PRIMARY_CI LOCATOR)
        # Enter value for primary course instance
        PRIMARY_COURSE_INSTANCE.send_keys(course_instance_1)

        SECONDARY_COURSE_INSTANCE = self.find_element(*By SECONDARY_CI LOCATOR)
        # Enter value for secondary course instance
        SECONDARY_COURSE_INSTANCE.send_keys(course_instance_2)

        # Click on Add to Pair Cross_Listing Course
        self.find_element(by Add Paring --Submit Locator)

    #TODO:  This is a stub only

    def confirm_alert_text(self):
        """
        :param self:
        :return: Confirms that an alert box returns after add indicating
        the presence of alert box.
        """
        alert_message = self.find_element(Locators.alert_box)
        if element is present:
            return True
        else:
            return False

    #TODO:  This is a stub only
    def confirm_success_alert_text(self, success/failure indicator_in_xls):
        """
        :param self:
        :return: Confirms that an alert box returns after add indicating
        the presence of alert box.
        """
        alert_message = self.find_element(Locators.alert_box)
        text = alert_message.text
        return text


    #TODO:  This is a stub only.
    def confirm_successful_add_by_id (self, course_instance_1,
                                      course_instance_2):
        """This confirms successful add by verifying that the
        course instance ID are on the search.  May not be needed if we're
        only checking by success or failure text only"""
        self.search_page = CrossListingBasePageObject(self.driver)
        element1 = self.search_page.get_cell_with_text(course_instance_1)
        element2 = self.search_page.get_cell_with_text(course_instance_2)


        if element 1 and element 2 is not none:
        #TO: can I condition this against if element1 AND element2 is on the page,
        # then return true and false? Look into how to write this

        #if element is not None:
            return True
        return False

