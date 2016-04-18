from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.course_info.course_info_base_test_case \
    import TEST_USERS_WITH_ROLES_PATH
from django.conf import settings

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


@ddt
class SingleAddPeopleTests(CourseInfoBaseTestCase):

    @data(*get_xl_data(TEST_USERS_WITH_ROLES_PATH))
    @unpack
    def test_add_person(self, test_case_id, test_user, canvas_role, role_id):
        """ verify the person search and add functionality for SINGLE-USER
        add"""

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
        self.assertFalse(self.people_page.people_added(1, 0))

        # add user to role
        self.people_page.search_and_add_users(test_user, canvas_role)

        # assert that user is found on page.
        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page. So this may change based on data changing
        self.assertTrue(self.people_page.is_person_on_page(test_user))

        # Assert that the success text is displayed
        self.assertTrue(self.people_page.people_added(1, 0))

        # clean up (avoid cluttering the course if multiple different
        # test users are used)
        self.api.remove_user(self.test_settings['test_course']['cid'],
                             test_user, role_id)


class MultipleAddPeopleTests(CourseInfoBaseTestCase):

    def setUp(self):
        """
        Common code: This method load up the course, and goes to
        the Course People Details page.
        """
        super(MultipleAddPeopleTests, self).setUp()
        self._load_test_course()
        self.detail_page.go_to_people_page()
        self.assertTrue(self.people_page.is_loaded())

        # Test data path for adding users
        self.test_data = settings.SELENIUM_CONFIG[
            'course_info_tool']['test_data_for_multiple_users_add']


    def test_multi_user_add_unsuccessful(self):
        """
        TLT-2574: AC #3, Test case 12
        This test verifies that that adding multiple users (for invalid ids)
        is unsuccessful.  Cleanup not needed via rest API for this test.
        """
        #  Add multiple invalid test ID
        self.people_page.search_and_add_users(self.test_data['unsuccessful_add'],
                                              self.test_data['canvas_role'])
        #  Verify that unsuccessful message shows up
        self.assertTrue(self.people_page.people_added(0, 2))

    def test_multi_user_add_successful(self):
        """
        TLT-2574: AC #3, Test case 12
        This test verifies that adding multiple users (for valid ID) is
        successful. Cleanup of data included.
        """
        # Put test data in a list, since rest api removes one id at a time.

        id_list = self.test_data['successful_add']

        # Remove test user if they are already in course.
        for user_id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'],
                                 user_id)

        # Search and add valid ID to the course
        # Join the id_list so we can pass in test users as a string; not list
        user_id_input_string = ', '.join(id_list)
        self.people_page.search_and_add_users(user_id_input_string,
                                              self.test_data['canvas_role'])
        self.driver.save_screenshot("add_users.png")


        ''' Limitation:  Due to pagination, this may not be a good test
        case if there are number of users in course.  In that case,
        we could go back to checking on alert text or expand the list of
        people displayed'''

        #  Verify successful add (if ID appears in the list of users)

        self.assertTrue(self.people_page.people_added(len(id_list), 0))
        #  Cleanup
        for user_id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'],
                                 user_id)
            self.assertTrue(self.people_page.is_person_on_page(user_id))

    def test_multiple_add_partial_failure(self):
        """
        TLT-2574: AC #3, Test case 12
        This test verifies that adding multiple users is partially successful.
        Cleanup of data included.
        """
        # test data as a list, since rest api removes user one at a time
        id_list = self.test_data['partial_success_add']

        # Remove test users if they are already in course.
        for id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'], id)

        # Join the id_list so we can pass in test users as a string; not list
        user_id_input_string = ', '.join(id_list)
        self.people_page.search_and_add_users(user_id_input_string,
                                             self.test_data['canvas_role'])
        # Verify that user is not added through alert text
        self.assertTrue(self.people_page.people_added(1, 1))
        self.people_page.is_person_on_page(id_list[0])

        # Test data cleanup from course
        for id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'], id)
