from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

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
                                                          secondary_cid)
        )

        # Verifies alert confirmation appears 
        self.assertTrue(
                self.index_page.confirm_presence_of_confirmation_alert()
        )

        # Verifies the cids are on page if it's successfully cross-listed
        if expected_result == 'success':
            self.assertTrue(self.index_page.is_add_successful())

        # Verifies error message if cross-listing is unsuccessful
        if expected_result == 'fail':
            expected_text = "EXPECTED ERROR MESSAGE" # TODO:need error
            actual_text = self.index_page.get_confirmation_text()
            self.assertEqual(actual_text, expected_text,
                             "Error. Expected error is '{}' but error is "
                             "returning '{}'".format(expected_text,
                                                     actual_text))

        # test_data must contain a value in expected result column.
        else:
            raise ValueError('given_access column for expected result {} must '
                             'be either '
                             '\'fail\' or \'success\''.format(expected_result)
                             )
