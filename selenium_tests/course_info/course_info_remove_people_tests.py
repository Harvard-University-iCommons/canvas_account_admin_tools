from ddt import ddt, data, unpack
from selenium_common.base_test_case import get_xl_data

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase, TEST_USERS_WITH_ROLES_PATH


@ddt
class RemovePeopleTests(CourseInfoBaseTestCase):

    @data(*get_xl_data(TEST_USERS_WITH_ROLES_PATH))
    @unpack
    def test_remove_person(self, test_case_id, test_user, canvas_role, role_id):
        """ Removes a user from course using the Admin Console """

        course_instance_id = self.test_settings['test_course']['cid']

        # Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        # environment (because of shared cache interactions)

        # ensure person is in course using API before attempting to remove in UI
        # 1. remove ALL roles/enrollments for the test user in this course
        #    to ensure no incidental data causes conflict when we try to add
        # 2. add via API the role we want to test removing through the UI
        self.api.remove_user(course_instance_id, test_user)
        self.api.add_user(course_instance_id, test_user, role_id)

        self._load_test_course()

        # asserts test user is on people page and to-be-removed user is on page
        self.assertTrue(self.people_page.is_person_on_page(test_user))

        # asserts that the delete confirmation text is not already on the page
        self.assertFalse(self.people_page.delete_was_successful())

        # deletes user and confirms that delete is successful
        self.people_page.delete_user(test_user)

        self.assertTrue(self.people_page.delete_was_successful())
        self.assertTrue(
            self.people_page.is_person_removed_from_list(test_user))
