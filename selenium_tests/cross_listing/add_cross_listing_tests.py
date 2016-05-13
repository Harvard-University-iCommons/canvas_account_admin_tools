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
        Jira requirement story: TLT-1314
        Selenium sub-task: TLT-2589.
        These tests cover AC #1 and #7.

        This test adds a valid cross-list pairing to the cross-listing table
        """
        # This adds a pairing to cross-list table, clicks submit,
        # and confirm an alert box appears.
        self.assertTrue(self.main_page.add_cross_listing_pairing(primary_cid,
                                                                 secondary_cid))

        # Verify a successful cross-list add
        if expected_result == 'success':

            # Removes cross-listed courses if it exists before testing add
            self.api.remove_xlisted_course(primary_cid, secondary_cid)

            #  Verifies successful add confirmation
            self.driver.save_screenshot("a_success_message.png")
            self.assertTrue(
                self.main_page.is_locator_text_present(expected_text))

            # Clean up and remove the cross-listed course when test is done
            self.api.remove_xlisted_course(primary_cid, secondary_cid)

        #  Verify an unsuccessful cross-list
        elif expected_result == 'fail':
            #  Verifies successful add confirmation
            self.assertTrue(
                self.main_page.is_locator_text_present(expected_text))

        else:
            raise ValueError(
                'given_access column for user {} must be either \'success\' '
                'or \'fail\''.format(expected_result)
            )
