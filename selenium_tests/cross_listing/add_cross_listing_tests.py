from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS


@ddt
class AddCrossListingTests(CrossListingBaseTestCase):

    @data(*get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_add_cross_listing_pairing(self, test_case,
                                       primary_cid,
                                       secondary_cid,
                                       expected_result,
                                       expected_text):
        """
        TLT-2589, AC #1 and 7
        This test adds a valid cross-list pairing to the cross-listing table
        """
        # This adds the pairing to the cross-list table and clicks submit
        self.main_page.add_cross_listing_pairing(primary_cid, secondary_cid)

        # This verifies that the confirmation box appears
        self.assertTrue(
                self.main_page.confirm_presence_of_confirmation_alert()
        )

        # Verifies a successful cross-list add
        if expected_result == 'success':

            #  Verifies successful add confirmation
            actual_text = self.main_page.get_actual_confirmation_text()
            expected_text = self.main_page.get_expected_confirmation_text(
                        expected_text)
            self.assertEqual(actual_text, expected_text,
                             "Error. Expected success message is '{}' but "
                             "message is returning '{}'".format(expected_text,
                                                                actual_text))

            # Clean up and remove the cross-listed course when test is done
            self.api.remove_xlisted_course(primary_cid, secondary_cid)

        #  Verifies an unsuccessful cross-list
        if expected_result == 'fail':
            actual_text = self.main_page.get_actual_confirmation_text()
            expected_text_on_page = \
                self.main_page.get_expected_confirmation_text(expected_text)
            self.assertEqual(actual_text, expected_text_on_page,
                             "Error: the error message locator cannot be "
                             "found. Expecting an error containing '{}' but "
                             "message is returning '{}'".format(
                                     expected_text, actual_text))
