from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


class PeopleListTests(CourseInfoBaseTestCase):

    def test_people_list_page_loaded(self):
        """verify the people search functionality"""

        course = self.test_settings['test_course']
        user = self.test_settings['test_users']['existing']

        # Note: ICOMMONS_REST_API_HOST environment needs to match the LTI tool
        # environment (because of shared cache interactions)

        # ensure person is in course using API before searching for them in UI
        # 1. remove ALL roles/enrollments for the test user in this course
        #    to ensure no incidental data causes conflict when we try to add
        # 2. add via API the role we want to test searching for in the UI
        self.api.remove_user(course['cid'], user['user_id'])
        self.api.add_user(course['cid'], user['user_id'], user['role_id'])

        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        # click on course link to view list of people in course
        self.search_page.select_course(cid=course['cid'])

        self.detail_page.go_to_people_page()

        # assert that an expected enrollment is present
        self.assertTrue(self.people_page.is_loaded())
        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page.
        self.assertTrue(self.people_page.is_person_on_page(user['user_id']))
