from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


class CourseInfoDetailsEditTests(CourseInfoBaseTestCase):


    def test_edit_fields(self):
        """
        verify editing fields in SB/ILE courses
        (capture original fields, edit, save, reload, verify against original)
        """

        # use the REST API to reset the field values before running the test
        # this could use DDT for various combinations of fields, if need be
        pass

    def test_regular_course_not_editable(self):
        """
        verify non-SB/ILE courses cannot be edited
        """

        pass

    def test_reset_form(self):
        """
        verify edit form reset button works as expected
        (capture original fields, edit, reset, verify against original)
        """

        pass
