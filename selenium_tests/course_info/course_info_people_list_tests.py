from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


class PeopleListTests(CourseInfoBaseTestCase):

    def test_people_list_page_loaded(self):
        """verify the people search functionality"""

        self._load_test_course()
        user = self.test_settings['test_users']['existing']['user_id']

        # scroll to the bottom to bring People link into view
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        # from details page, click people page
        self.detail_page.go_to_people_page()
        # Note: If the course has a lot of people enrolled, results are
        # paginated and it's possible that user may not be on the initial
        # page.
        self.assertTrue(self.people_page.is_person_on_page(user))
