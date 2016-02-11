from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


class RemovePeopleTest(CourseInfoBaseTestCase):

    def test_remove_person(self):
        """ Removes a user from course using the Admin Console """

        course_instance_id = self.test_settings['test_course']['cid']
        test_user = self.test_settings['test_users']['existing']
        test_user_id = test_user['user_id']
        test_user_role_id = test_user['role_id']

        # Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        # environment (because of shared cache interactions)

        # ensure person is in course using API before attempting to remove in UI
        # 1. remove ALL roles/enrollments for the test user in this course
        #    to ensure no incidental data causes conflict when we try to add
        # 2. add via API the role we want to test removing through the UI
        self.api.remove_user(course_instance_id, test_user_id)
        self.api.add_user(course_instance_id, test_user_id, test_user_role_id)

        self._load_test_course()

        # asserts test user is on people page and to-be-removed user is on page
        self.assertTrue(self.people_page.is_person_on_page(test_user_id))

        # asserts that the delete confirmation text is not already on the page
        self.assertFalse(self.people_page.delete_was_successful())

        # deletes user and confirms that delete is successful
        self.people_page.delete_user(test_user_id)

        self.assertTrue(self.people_page.delete_was_successful())
        self.assertTrue(
            self.people_page.is_person_removed_from_list(test_user_id))
