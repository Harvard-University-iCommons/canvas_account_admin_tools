from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.course_info.course_info_base_test_case \
    import TEST_USERS_WITH_ROLES_PATH
from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


@ddt
class AddPeopleTests(CourseInfoBaseTestCase):

    @data(*get_xl_data(TEST_USERS_WITH_ROLES_PATH))
    @unpack
    def test_add_person(self, test_case_id, test_user, canvas_role, role_id):
        """ verify the person search and add functionality """

        # Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        # environment (because of shared cache interactions)

        # ensure person is not in course before attempting to add using API;
        # remove ALL roles/enrollments for the test user in this course
        # to ensure no incidental data causes conflict when we try to add
        self.api.remove_user(self.test_settings['test_course']['cid'],
                             test_user)

        self._load_test_course()

        self.detail_page.go_to_people_page()

        # search for a user and add user to course
        self.assertTrue(self.people_page.is_loaded())

        # assert that the success message is not already loaded on the page
        self.assertFalse(self.people_page.add_was_successful())

        # add user to role
        self.people_page.search_and_add_user(test_user, canvas_role)

        # assert that user is found on page.
        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page. So this may change based on data changing
        self.assertTrue(self.people_page.is_person_on_page(test_user))

        # Assert that the success text is displayed
        self.assertTrue(self.people_page.add_was_successful())

        # clean up (avoid cluttering the course if multiple different
        # test users are used)
        self.api.remove_user(self.test_settings['test_course']['cid'],
                             test_user, role_id)

