from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS

@ddt
class RemoveCrossListingTests(CrossListingBaseTestCase):

    @data(*get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_remove_mapping(self, test_case_id, primary_cid,
                            secondary_cid, expected_result,
                            expected_alert_text):

        """
        Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        environment (because of shared cache interactions)

        1. remove existing cross-list mappings via rest api first to
        avoid incidental conflict when we try to add a new mapping.
        2. add via cross-listing via rest api that we want to remove
        3. test remove by clicking on the cross-list remove icon via UI
        """
        # Remove tests only apply those those cases where there is an expected
        # successful add.
        if expected_result == 'success':
            # Remove xlisted pairing - if it exists - via rest api first
            # for a clean test.
            self.api.remove_xlisted_course(primary_cid, secondary_cid)

            # Add the xlisted pair via rest api
            self.api.add_xlisted_course(primary_cid, secondary_cid)

            # Get the xlist_map_id so look for the delete icon
            xlist_map_id = self.api.lookup_xlist_map_id(primary_cid,
                                                        secondary_cid)

            # Reload cross_listing_page due to changes from REST API Add.
            if not self.acct_admin_dashboard_page.is_loaded():
                self.acct_admin_dashboard_page.get(self.TOOL_URL)
            # navigate to cross-list tool
            self.acct_admin_dashboard_page.select_cross_listing_link()

            # Clicks on the delete icon associated with the xlist_map_id
            self.main_page.delete_cross_listing_pairing(xlist_map_id)

            # Verifies pair has been de-crosslisted by confirmation message
            expected_text = "Successfully de-cross-listed {} and {}.".format(
                                                    primary_cid, secondary_cid)
            actual_text = self.main_page.get_actual_confirmation_text()
            self.assertEqual(actual_text, expected_text,
                             "Expected success message is '{}' but message is "
                             "returning '{}'".format(expected_text, actual_text)
                             )
