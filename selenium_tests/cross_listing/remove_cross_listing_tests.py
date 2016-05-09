from ddt import ddt, data, unpack
from selenium_common.base_test_case import get_xl_data

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS


@ddt
class RemoveCrossListingTests(CrossListingBaseTestCase):

    @data(*get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_remove_mapping(self, test_case_id, primary_cid,
                            secondary_cid, expected_result):

        """ Removes cross-listing mappings

        Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        environment (because of shared cache interactions)

        1. remove ALL course instance mappings that matches primary or
        secondary ids, to ensure no incidental data causes conflict when
        we try to add
        2. add via api the mapping we want to remove through the UI
        3. remove cross-listing pair via UI
        """

        # Remove any xlisted pairing via rest api for a clean test.
        self.api.remove_xlisted_course(primary_cid)

        # Add the xlisted pair via rest api
        self.api.add_xlisted_course(primary_cid, secondary_cid)

        # Remove via UI









