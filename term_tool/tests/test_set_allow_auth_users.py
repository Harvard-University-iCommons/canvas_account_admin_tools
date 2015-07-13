from django.test import TestCase
from mock import patch, ANY
from term_tool.management.commands.set_allow_auth_users import process_terms
from canvas_sdk.exceptions import CanvasAPIError


@patch('term_tool.management.commands.set_allow_auth_users.logger.info')
@patch('term_tool.management.commands.set_allow_auth_users.logger.error')
@patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
@patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
@patch('term_tool.management.commands.set_allow_auth_users.update_course')
class CommandsTestSyncCanvasSections(TestCase):
    """
    tests for the sync_canvas_sections management command.
    these are unit tests for the helper methods in the command. The command itself
    really needs to be integration tested with the database.
    """

    def test_process_terms_valid_term(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Test that CourseInstance.objects.filter is called if a term is found (without incremental argument)
        """
        m_term.return_value.values_list.return_value = [1]
        process_terms(allow_access=True, sis_term_id=1)
        m_ci.assert_called_once_with(sync_to_canvas=True, term=1, exclude_from_shopping=False)

    def test_process_terms_multiple_terms(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Courses should be fetched for each term if multiple shoppable terms found
        """
        m_term.return_value.values_list.return_value = [1, 2]
        m_ci.return_value.values_list.side_effect = [[12345], [23456]]
        process_terms(allow_access=False)
        self.assertEqual(m_sdk.call_count, 2)

    def test_process_terms_multiple_courses(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        SDK should be called once per course in courses_to_process
        """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = [12345, 23456]
        process_terms(allow_access=False, sis_term_id=1)
        self.assertEqual(m_sdk.call_count, 2)

    def test_process_terms_invalid_term(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Log the correct message if requested term is not found or not shoppable
        """
        m_term.return_value.values_list.return_value = []
        process_terms(allow_access=True, sis_term_id=123)
        self.assertEqual(m_log_i.call_count, 1)
        args, kwargs = m_log_i.call_args_list[0]
        self.assertGreaterEqual(args[0].find('not found'), 0)

    def test_process_terms_no_shoppable_terms(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Log the correct message if no shoppable terms are found
        """
        m_term.return_value.values_list.return_value = []
        process_terms(allow_access=True)
        args, kwargs = m_log_i.call_args_list[0]
        self.assertGreaterEqual(args[0].find('No terms'), 0)

    def test_process_terms_no_course_id_found(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        SDK should not be called if no course_id is found for a course
        """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = []
        process_terms(allow_access=False, sis_term_id=1)
        self.assertEqual(m_sdk.call_count, 0)

    def test_process_terms_sdk_call_set_true(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Test that the sdk is called with the correct params set to true
        """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = [12345]
        process_terms(allow_access=True, sis_term_id=1)
        m_sdk.assert_called_with(ANY, 'sis_course_id:12345', course_is_public_to_auth_users=True)

    def test_process_terms_sdk_call_set_false(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Test that the sdk is called with the correct params set to false
        """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = [12345]
        process_terms(allow_access=False, sis_term_id=1)
        m_sdk.assert_called_with(ANY, 'sis_course_id:12345', course_is_public_to_auth_users=False)

    def test_process_sdk_exception(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """
        Test that error logger is called if the sdk call throws an exception
        """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = [12345]
        m_sdk.side_effect = CanvasAPIError()
        process_terms(allow_access=False, sis_term_id=1)
        self.assertEqual(m_log_e.call_count, 1)
        args, kwargs = m_log_e.call_args
        self.assertGreaterEqual(args[0].find('CanvasAPIError'), 0)

    def test_process_terms_with_interval_matches(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """ SDK should be called if courses are found within the expected interval """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = [12345]
        process_terms(allow_access=False, sis_term_id=1, interval_in_minutes=5)
        m_ci.assert_called_once_with(term=1, exclude_from_shopping=False, sync_to_canvas=True, last_updated__gte=ANY)
        self.assertEqual(m_sdk.call_count, 1)

    def test_process_terms_with_interval_no_matches(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """ SDK should not be called if no courses are found within the expected interval """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = []
        process_terms(allow_access=False, sis_term_id=1, interval_in_minutes=5)
        m_ci.assert_called_once_with(term=1, exclude_from_shopping=False, sync_to_canvas=True, last_updated__gte=ANY)
        self.assertEqual(m_sdk.call_count, 0)

    def test_process_terms_dry_run(self, m_sdk, m_term, m_ci, m_log_e, m_log_i):
        """ Dry run should not actually call update courses """
        m_term.return_value.values_list.return_value = [1]
        m_ci.return_value.values_list.return_value = [12345]
        process_terms(allow_access=False, sis_term_id=1, dry_run=True)
        self.assertEqual(m_sdk.call_count, 0)
