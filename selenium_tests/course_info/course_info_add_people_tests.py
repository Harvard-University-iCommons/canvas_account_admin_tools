from ddt import ddt, data, unpack

from selenium_common.base_test_case import get_xl_data
from selenium_tests.course_info.course_info_base_test_case \
    import TEST_USERS_WITH_ROLES_PATH, ADD_MULTIPLE_USERS_PATH
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


@ddt
class MultipleAddPeopleTests(CourseInfoBaseTestCase):

    @data(*get_xl_data(ADD_MULTIPLE_USERS_PATH))
    @unpack
    def test_multi_add_unsuccessful(self, test_case_id, test_user,
                                      canvas_role, role_id):

        # This test is testing that ID are not successfully added.

        self._load_test_course()
        self.detail_page.go_to_people_page()
        # verify that you are on the course's people's page
        self.assertTrue(self.people_page.is_loaded())

        # add TWO users to role
        self.people_page.search_and_add_user(test_user, canvas_role)
        self.driver.save_screenshot('people_add.png')

        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page. So we are asserting the alert message instead

        #debug
        element = self.driver.find_element_by_id('alert-success').text
        element1 = element.strip()
        print element1

        #TODO: this assert is failing here, could not find text on page (?)
        self.assertTrue(self.people_page.add_was_unsuccessful())

        # debug 
        # self.driver.find_element_by_xpath('//p[contains(.,"could not be
        # added.")]')


    # def test_successful_multi_user_add self):
    #     """
    #     Test multiple add where add is successful
    #     rest API call/cleanup for this one.
    #    :return:
    #     Failure message on screen that user is not found
    #     """

    # def test_multiple_add_partial_failure_due_to_user_not_found(self):
    #     """
    #     Test multiple add where a user is not found (fake ID)
    #     No need to do rest API call/cleanup for this one.
    #    :return:
    #     Failure message on screen that user is not found
    #     """
    #
    # def test_multiple_add_partial_failure_due_to_user_already_added (self):
    #     """
    #     Test multiple add where one user is already added
    #     Need rest API cleanup for the partial success
    #     :return:
    #     Failure message on screen that user is already added
    #     """
    #
    # def test_multiple_add_full_failure_no_user_gets_added(self):
    #     """
    #     Test multiple add where one user is already added
    #     Need rest API cleanup for the partial success
    #     :return:
    #     Failure message on screen that no ID is added
    #     """
    #
