from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase
from selenium_tests.course_info.page_objects.course_info_detail_page_object \
    import CourseInfoDetailPageObject


class CourseInfoDetailsEditTests(CourseInfoBaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.details_page = CourseInfoDetailPageObject(cls.driver)

    def setUp(self):
        self._load_test_course('test_course_SB_ILE')
        self.assertTrue(self.details_page.is_loaded())

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

        original_field_values = {}
        test_fields = [
            'description',
            'instructors_display',
            'location',
            'meeting_time',
            'notes',
            'short_title',
            'sub_title',
            'title'
        ]

        for f in test_fields:
            original_field_values[f] = self.details_page.get_input_field_text(f)
            changed_text = '(changed) {}'.format(original_field_values[f])
            self.details_page.enter_text_in_input_field(f, changed_text)
            self.assertEqual(self.details_page.get_input_field_text(f),
                             changed_text)

        self.details_page.reset_form()

        for f in test_fields:
            self.assertEqual(self.details_page.get_input_field_text(f),
                             original_field_values[f])
