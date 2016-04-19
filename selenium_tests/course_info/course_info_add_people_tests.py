from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.course_info.course_info_base_test_case \
    import TEST_USER_SEARCH_TERMS_PATH

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


@ddt
class AddPeopleTests(CourseInfoBaseTestCase):

    @data(*get_xl_data(TEST_USER_SEARCH_TERMS_PATH))
    @unpack
    def test_add_people(self, test_case_id, search_terms, canvas_role, role_id,
                        successes, failures):
        """ verify the person search and add functionality """

        # Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        # environment (because of shared cache interactions)

        # ensure people are not in course before attempting to add using API;
        # remove ALL roles/enrollments for the test users in this course
        # to ensure no incidental data causes conflict when we try to add

        test_course_key = 'test_course_SB_ILE'
        test_cid = self.test_settings[test_course_key]['cid']
        id_list = [s.strip() for s in search_terms.split(',')]

        for user_id in id_list:
            self.api.remove_user(test_cid, user_id)

        self._load_test_course('test_course_SB_ILE')

        self.detail_page.go_to_people_page()

        # search for a user and add user to course
        self.assertTrue(self.people_page.is_loaded())

        # assert that the results message is not already loaded on the page
        self.assertFalse(self.people_page.people_added(int(successes), int(failures)))

        # add user to role
        self.people_page.search_and_add_users(search_terms, canvas_role)

        # Assert that the results summary text is displayed
        self.assertTrue(self.people_page.people_added(int(successes), int(failures)))

        # clean up (avoid cluttering the course if multiple different
        # test users are used)
        for user_id in id_list:
            self.api.remove_user(test_cid, user_id)
