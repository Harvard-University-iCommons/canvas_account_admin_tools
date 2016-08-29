from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS


@ddt
class AddCrossListingTests(CrossListingBaseTestCase):

    @data(*get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_add_cross_listing_pairing(self, _unused_test_case_id,
                                       primary_cid,
                                       secondary_cid,
                                       expected_result,
                                       expected_alert_text):
        """
        Jira requirement story: TLT-1314
        Selenium sub-task: TLT-2589.
        These tests cover AC #1 and #7.

        This test adds a valid cross-list pairing to the cross-listing table
        """

        if expected_result not in ['success', 'fail']:
            raise ValueError(
                'given_access column for user {} must be either \'success\' '
                'or \'fail\''.format(expected_result))

        # Removes cross-listed courses if it exists before testing add
        try:
            self.api.remove_xlisted_course(primary_cid, secondary_cid)
        except RuntimeError as e:
            if 'CanvasAPIError' in e.message and \
                    'section is not cross-listed' in e.message:
                # this is a known possibility with test cases that
                # result in a partial success (e.g. the Canvas side failed)
                pass
            else:
                raise e

        # This adds a pairing to cross-list table, clicks submit,
        # and confirm an alert box appears.
        self.assertTrue(self.main_page.add_cross_listing_pairing(primary_cid,
                                                                 secondary_cid))
        #  Verifies expected alert text
        #  (e.g. confirmation if successful, error message if unsuccessful)
        self.assertTrue(
            self.main_page.confirmation_contains_text(expected_alert_text))

        # Verify a successful cross-list add
        if expected_result == 'success':
            # Clean up and remove the cross-listed course when test is done
            self.api.remove_xlisted_course(primary_cid, secondary_cid)
