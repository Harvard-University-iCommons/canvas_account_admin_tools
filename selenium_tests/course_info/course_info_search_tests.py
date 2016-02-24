from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


class CourseSearchTests(CourseInfoBaseTestCase):

    def test_course_search(self):
        """verify the course search functionality"""

        course = self.test_settings['test_course']

        self.search_for_course(
            type=course['type'], school=course['school'], term=course['term'],
            year=course['year'], search_term=course['cid'])

        self.assertTrue(self.search_page.is_course_displayed(cid=course['cid']))
