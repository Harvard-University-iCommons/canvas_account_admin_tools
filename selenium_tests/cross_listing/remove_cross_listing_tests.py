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

        # 1. Remove existing test records if any
        # reference from remove_user is:
        # self.api.remove_user(course_instance_id, test_user)
        # lookup xlist_maps Id, then delete that id record

        # 2. Add mappings via API
        # reference from add_user is:
        # self.api.add_user(course_instance_id, test_user, role_id)
        # post to xlist_maps/ path

        # 3. Remove cross-listing mapping via UI
        # Delete a cross-listed pair via UI and verify message
