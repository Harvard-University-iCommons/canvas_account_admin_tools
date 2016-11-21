from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_common.canvas.canvas_masquerade_page_object \
    import CanvasMasqueradePageObject
from selenium_tests.bulk_create.bulk_create_base_test_case \
    import BulkCreateBaseTestCase
from selenium_tests.bulk_create.bulk_create_base_test_case \
    import CANVAS_PERMISSION_ROLES
from selenium_tests.bulk_create.page_objects.index_page import IndexPageObject


@ddt
class BulkCreatePermissionTests(BulkCreateBaseTestCase):
    @data(*get_xl_data(CANVAS_PERMISSION_ROLES))
    @unpack
    def test_roles_access(self, user_id, given_access):
        """
        This test masquerades as various roles from the test data spreadsheet
        and verifies that user in said role should or should not be granted
        access to the Course Bulk Creator.
        """

        masquerade_page = CanvasMasqueradePageObject(self.driver,
                                                     self.canvas_base_url)
        index_page = IndexPageObject(self.driver)

        # Masquerade as a user defined in the Test_Data/Roles Access spreadsheet
        masquerade_page.masquerade_as(user_id)

        # Once masqueraded as user, go to Course Create Tool
        self.driver.get(self.base_url)

        if given_access == 'no':
            print "Verifying user %s is denied access to course bulk create " \
                  "tool" % user_id
            self.assertFalse(index_page.is_authorized(),
                             'User {} unexpectedly authorized'.format(user_id))

        elif given_access == 'yes':
            print "Verifying user %s is granted access to course bulk create " \
                  "tool" % user_id
            self.assertTrue(index_page.is_authorized(),
                            'User {} unexpectedly denied access'.format(
                                user_id))

        else:
            raise ValueError('given_access column for user {} must be either '
                             '\'yes\' or \'no\''.format(user_id))
