from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_common.base_page_object import BasePageObject

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS


@ddt
class AddCrossListingTests(CrossListingBaseTestCase):

    """TLT-2589, AC #1 and 7
    This test adds a valid cross-list pairing to the cross-listing table
    """

    @data(get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_adding_a_cross_listing_pairing(self, test_case_id,
                                            primary_cid, secondary_cid,
                                            expected_result):

        # TODO: This is a test stub only:

        # Adds the pairing
        self.assertTrue(
                self.index_page.add_cross_listing_pairing(primary_cid,
                                                          secondary_cid))

        # Verifies alert confirmation appears on page
        self.assertTrue(
                self.index_page.confirm_presence_of_some_alert_box())

        # Verifies that that course is added successfully or failed,
        # based on either search by ID or by confirmation text only - TBD

        self.assertTrue(
                self.index_page._confirm_based_on_alert_text_or_search_by_text_on_page()
        # TODO:  based on expected result?