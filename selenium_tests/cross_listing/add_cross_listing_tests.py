from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase
from selenium_tests.cross_listing.page_objects.cross_listing_main_page import\
    MainPageObject

from selenium_common.base_page_object import BasePageObject


class AddCrossListingTests(CrossListingBaseTestCase):

    """TLT-2589, AC: TBD """

    def test_adding_a_cross_listing_pairing(self, course_instance_1,
                                            course_instance_2):

        """This test adds a valid cross-list pairing to the cross-listing table
        Removal of mapping will be covered in a future story. Cleanup
        via UI or rest API (?) required.
        """
        # TODO: This test should not go in until remove is in place

        # TODO:  Think about data, perhaps valid and invalid data can just be
        #  in one spreadsheet, but test is conditioned against some text?

        course_instance1 = self.test_data(get_test_data_from_local or xls)
        course_instance2 = self.test_data(get_test_data_from_local or xls)

        # STUB:
        # Adds the pairing
        self.assertTrue(
                self.index_page.add_cross_listing_pairing())
        # Verifies alert confirmation appears on page
        self.assertTrue(
                self.index_page.confirm_presence_of_some_alert_box())
        # Verifies that that course is added successfully or failed,
        # based on either search by ID or by confirmation messasge only
        self.assertTrue(
                self.index_page._confirm_alert_text()

