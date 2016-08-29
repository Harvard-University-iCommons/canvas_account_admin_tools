from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS

@ddt
class RemoveCrossListingTests(CrossListingBaseTestCase):

    @data(*get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_remove_and_search_successful(self, _unused_test_case_id,
                                          primary_cid,
                                          secondary_cid,
                                          expected_result,
                                          _unused_expected_alert_text):

        """
        Jira requirement stories: TLT-1979 (remove), TLT-2670 (search
        Selenium sub-task: TLT-2595.
        These tests cover AC #1 and #2.

        The test is performing these steps:
        1.  Remove  existing cross-list mappings via rest api first to
        avoid incidental conflict when we try to add a new mapping.
        2.  Add cross-listing via rest api of the pairing that we
        want to test the 'remove' functionality on.
        3.  Find this new cross-listing using the search box
        4.  Test remove by clicking on the cross-list remove icon via UI

        """
        # Remove tests only apply those those cases where there is an expected
        # successful add.
        if expected_result == 'success':
            # Remove xlisted pairing - if it exists - via rest api first
            # for a clean test.
            self.api.remove_xlisted_course(primary_cid, secondary_cid)

            # Add the xlisted pair via rest api
            self.api.add_xlisted_course(primary_cid, secondary_cid)

            # Get the xlist_map_id to locate the right delete icon
            xlist_map_id = self.api.lookup_xlist_map_id(primary_cid,
                                                        secondary_cid)

            # Search for the new cross-listing so it is on the first page of
            # results and therefore clickable
            self.main_page.search('{} {}'.format(primary_cid, secondary_cid))

            # Clicks on the delete icon associated with the xlist_map_id.
            # Known limitation: this works only if the cross-listing pairing is
            # on the first page of results presently shown.
            self.main_page.delete_cross_listing_pairing(xlist_map_id)

            # Verifies pair has been de-crosslisted by confirmation message
            expected_text = "Successfully de-cross-listed {} and {}.".format(
                                                    primary_cid, secondary_cid)
            actual_text = self.main_page.get_confirmation_text()
            # Checks that the de-cross-list message appears.
            self.assertEqual(actual_text, expected_text)
