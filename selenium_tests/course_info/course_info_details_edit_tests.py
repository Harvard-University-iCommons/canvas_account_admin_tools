

from selenium_tests.course_info.course_info_base_test_case \
    import CourseInfoBaseTestCase


class CourseInfoDetailsEditTests(CourseInfoBaseTestCase):
    editable_fields = [
        'description',
        'instructors_display',
        'location',
        'meeting_time',
        'notes',
        'short_title',
        'sub_title',
        'title'
    ]

    def test_edit_fields(self):
        """
        TLT-2523 (AC 2-11)
        verify editing fields in SB/ILE courses
        (capture original fields, edit, save, reload, verify against original)
        """

        # use the REST API to reset the field values before running the test

        patch_data = {}
        for f in self.editable_fields:
            patch_data[f] = f  # just set the field value to the field name

        course_instance_id = self.test_settings['test_course_SB_ILE']['cid']
        self.api.patch_course_instance_details(course_instance_id, patch_data)

        self._load_test_course('test_course_SB_ILE')
        self.assertTrue(self.detail_page.is_loaded())

        original_field_values = {}
        new_field_values = {f: '(changed) {}'.format(patch_data[f])
                            for f in self.editable_fields}

        self.detail_page.edit_form()

        for f in self.editable_fields:
            original_field_values[f] = self.detail_page.get_input_field_value(f)
            self.assertEqual(original_field_values[f], patch_data[f])
            self.detail_page.enter_text_in_input_field(f, new_field_values[f])
            self.assertEqual(self.detail_page.get_input_field_value(f),
                             new_field_values[f])

        self.detail_page.submit_form()
        self.assertTrue(self.detail_page.submit_was_successful())

        # check values saved to database via API

        api_data = self.api.get_course_instance_details(course_instance_id)

        for f in self.editable_fields:
            self.assertEqual(api_data[f], new_field_values[f])

    def test_reset_form(self):
        """
        TLT-2524 (AC 1, 2)
        TLT-2525 (AC 22)
        verify edit form reset button works as expected
        (capture original fields, edit, reset, verify against original)
        """

        self._load_test_course('test_course_SB_ILE')
        self.assertTrue(self.detail_page.is_loaded())

        original_field_values = {}

        self.detail_page.edit_form()

        for f in self.editable_fields:
            original_field_values[f] = self.detail_page.get_input_field_value(f)
            changed_text = '(changed) {}'.format(original_field_values[f])
            self.detail_page.enter_text_in_input_field(f, changed_text)
            self.assertEqual(self.detail_page.get_input_field_value(f),
                             changed_text)

        self.detail_page.reset_form()

        self.detail_page.edit_form()

        for f in self.editable_fields:
            self.assertEqual(self.detail_page.get_input_field_value(f),
                             original_field_values[f])
