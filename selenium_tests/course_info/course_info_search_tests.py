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

    # If a course has a defined registrar_code_display in the db, then the
    # registrar_code_display should appear under the 'Course Code' column
    # If a course does not have a defined registrar_code_display in the db
    # (i.e. if that field is null), then the registrar_code should appear
    # under the 'Course Code' column (TLT-2511)
    # https://jira.huit.harvard.edu/browse/TLT-2521

    def test_registrar_code_when_registrar_code_display_is_null(self):
        """
        Test when course has a registrar_code_display that is null in db.
        Expected result: Course Code will display the registrar_code
        :return:
        """
        course = self.test_settings[
            'test_course_with_registrar_code_display_not_populated_in_db']

        self.search_for_course(
            school=course['school'],
            search_term=course['cid'])

        self.assertEqual(self.search_page.get_text(
            course['registrar_code_display']),
            course['registrar_code_display'],
            "Registrar code display does not match the expected text: "
            "{}".format(course['registrar_code_display']))

    def test_registrar_code_when_registrar_code_display_is_not_null(self):
        """
        Test when course has a registrar_code_display that is not null in db.
        Expected result: Course Code will display the registrar_code_display
        :return:
        """
        course = self.test_settings['test_course']

        self.search_for_course(
            school=course['school'],
            search_term=course['cid'])

        self.assertEqual(self.search_page.get_text(
            course['registrar_code_display']),
            course['registrar_code_display'],
            "Registrar code display does not match the expected text: "
            "{}".format(course['registrar_code_display']))
