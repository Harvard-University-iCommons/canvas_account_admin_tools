from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data

from selenium_tests.cross_listing.cross_listing_base_test_case import \
    CrossListingBaseTestCase, TEST_DATA_CROSS_LISTING_MAPPINGS


@ddt
class PublishCoursesTests(CrossListingBaseTestCase):

    @data(*get_xl_data(TEST_DATA_CROSS_LISTING_MAPPINGS))
    @unpack
    def test_publish_courses(self)
        """ Jira-1850 """

        #TODO:
            # Select a term
            # Test the publish button
            # Verify confirmation message
            # Verify grayed out option
            # cleanup