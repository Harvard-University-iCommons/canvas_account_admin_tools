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

    def test_course_code_is_display_when_registrar_code_display_is_null(self):
        """
        This test will verify that if the registrar_code_display in the
        database is null, that the user will see the registrar_code
        that was entered
        """

        course = self.test_settings['test_course_with_null']

        self.search_for_course(
            school=course['school'],
            search_term=course['cid'])

        self.assertTrue(self.search_page.is_course_code_visible(
            course['registrar_code_display']))

    def test_course_code_display_when_registrar_code_display_is_not_null(self):
        """
        This test will verify that if the registrar_code_display in the
        database is null, that the user will see the registrar_code
        that was entered
        """

        course = self.test_settings['test_course']

        self.search_for_course(
            school=course['school'],
            search_term=course['cid'])

        self.assertTrue(self.search_page.is_course_code_visible(
            course['registrar_code_display']))

    def test_registrar_code_when_registrar_code_display_is_null(self):
        """
        Test when registrar_code_display is null.
        Expected result: Course Code will display the registrar_code
        :return:
        """
        course = self.test_settings['test_course_with_null']

        self.search_for_course(
            school=course['school'],
            search_term=course['cid'])

        self.assertEqual(self.search_page.get_text(
            course['registrar_code_display']),
            course['registrar_code_display'],
            "Registrar code display does not equal")

    def test_registrar_code_when_registrar_code_display_is_not_null(self):
        """
        Test when registrar_code_display is not null.
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
            "Registrar code display does not equal")
