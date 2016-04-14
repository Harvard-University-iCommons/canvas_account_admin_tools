from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.course_info.course_info_base_test_case \
    import TEST_USERS_WITH_ROLES_PATH
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


class MultipleAddPeopleTests(CourseInfoBaseTestCase):

    def _load_find_info_tool(self):
        """
        Common code: This method loads up the find_info_tool and goes to the
        People's page
        """
        self._load_test_course()
        self.detail_page.go_to_people_page()
        self.assertTrue(self.people_page.is_loaded())


    def test_multi_user_add_unsuccessful(self):
        """
        TLT-2574
        This test verifies that multiple_user_add (for invalid ID) is
        unsuccessful.  Cleanup not needed via rest API for this test.
        """
        # Load up test course and go to People Page
        self._load_find_info_tool()

        # Add multiple invalid test ID
        self.people_page.search_and_add_user(self.test_data['unsuccessful_add'],
                                             self.test_data['canvas_role'])
        # Verify that unsuccessful message shows up
        self.assertTrue(self.people_page.add_was_unsuccessful())

    def test_multi_user_add_successful(self):
        """
        TLT-2574:
        This test verifies that multiple_user_add (for valid ID) are successful.
        Cleanup of data required and included via rest API calls.
        """
        # Put test data in a list, since rest api removes one id at a time.
        id_list = self.test_data['successful_add']

        # Remove test user if they are already in course.
        for user_id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'],
                                 user_id)

        # Load up the test course and go to People Page
        self._load_find_info_tool()

        # Join the id_list so we can pass in test users as a string; not list
        element = ', '.join(id_list)
        # Search and add valid ID to the course
        self.people_page.search_and_add_user(element, self.test_data['canvas_role'])

        ''' Limitation:  This may no longer be a valid test if there are a lot
        of ID in the test course and the user being added appears
        on second page due to pagination.  If that is the case, we could go
        back to checking on alert text'''

        # Verify successful add (if ID appears in the list of users)
        for user_id in id_list:
            self.people_page.add_is_successful_by_id(user_id)
            # Clean up test data at the end of test
            self.api.remove_user(self.test_settings['test_course']['cid'],
                                 user_id)


    def test_multiple_add_partial_failure(self):
        """
        TLT-2574:
        This test verifies that multiple_user_add is partially successful.
        Some added.  Others aren't. Cleanup of data includedincluded.
        """
        # test data as a list, since rest api removes user one at a time
        id_list = self.test_data['partial_success_add']

        # Remove test users if they are already in course.
        for id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'], id)

        #  Load up test course and go to People page.
        self._load_find_info_tool()

        # Join the id_list so we can pass in test users as a string; not list
        element = ', '.join(id_list)
        self.people_page.search_and_add_user(element,
                                             self.test_data['canvas_role'])

        # Verify that user is not added through alert text
        self.assertTrue(self.people_page.multiple_add_partial_failure())

        # Test data cleanup from course
        for id in id_list:
            self.api.remove_user(self.test_settings['test_course']['cid'], id)

