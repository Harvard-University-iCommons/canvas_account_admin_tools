from django.test import TestCase
from mock import patch, ANY
from term_tool.management.commands.set_allow_auth_users import process_terms
from canvas_sdk.exceptions import CanvasAPIError


class CourseInstanceStub:
    """
    Stub for a course instance object
    """

    def __init__(self, course_instance_id):
        self.course_instance_id = course_instance_id

    def get(self, string=None):
        return self.course_instance_id


class TermStub:
    """
    Stub for a Term object
    """

    def __init__(self, term_id, school_id):
        self.term_id = term_id
        self.school_id = school_id


class ValuesStub:
    """
    Stub for values method on database call
    """

    def __init__(self, data):
        self.data = data

    def values(self, somestring=None):
        return self.data


class CommandsTestSyncCanvasSections(TestCase):
    """
    tests for the sync_canvas_sections management command.
    these are unit tests for the helper methods in the command. The command itself
    really needs to be integration tested with the database.
    """
    # def setUp(self):
    #
    # self.course_instance = CourseInstanceStub(123456)

    @patch('term_tool.management.commands.set_allow_auth_users.logger.info')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_invalid_term(self, mock_term, mock_logger):
        """
        Log the correct message if requested term is not found or not shoppable
        """
        mock_term.return_value = []
        process_terms('true', term_id=123)
        self.assertEqual(mock_logger.call_count, 1)
        args, kwargs = mock_logger.call_args
        self.assertGreaterEqual(args[0].find('not found'), 0)

    @patch('term_tool.management.commands.set_allow_auth_users.logger.info')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_no_shoppable_terms(self, mock_term, mock_logger):
        """
        Log the correct message if no shoppable terms are found
        """
        mock_term.return_value = []
        process_terms('true')
        self.assertEqual(mock_logger.call_count, 1)
        args, kwargs = mock_logger.call_args
        self.assertGreaterEqual(args[0].find('No terms'), 0)

    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_valid_term(self, mock_term, mock_ci):
        """
        Test that CourseInstance.objects.filter is called if a term is found
        """
        mock_term.return_value = [TermStub(1, 'colgsas')]
        process_terms('true', term_id=1)
        mock_ci.assert_called_with(sync_to_canvas=True, term=1, exclude_from_shopping=False)

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_valid_term_valid_set_true_course_sdk_call(self, mock_term, mock_ci, mock_sdk):
        """
        Test that the sdk is called with the correct params set to true
        """
        mock_term.return_value = [TermStub(1, 'colgsas')]
        mock_ci.return_value = ValuesStub([CourseInstanceStub(course_instance_id=12345)])
        process_terms('true', term_id=1)
        mock_sdk.assert_called_with(ANY, 'sis_course_id:12345', 'sis_account_id:colgsas',
                                    course_is_public_to_auth_users='true')

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_valid_term_valid_set_false_course_sdk_call(self, mock_term, mock_ci, mock_sdk):
        """
        Test that the sdk is called with the correct params set to false
        """
        mock_term.return_value = [TermStub(1, 'colgsas')]
        mock_ci.return_value = ValuesStub([CourseInstanceStub(course_instance_id=12345)])
        process_terms('false', term_id=1)
        mock_sdk.assert_called_with(ANY, 'sis_course_id:12345', 'sis_account_id:colgsas',
                                    course_is_public_to_auth_users='false')

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.logger.error')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_sdk_exception(self, mock_term, mock_logger, mock_ci, mock_sdk):
        """
        Test that error logger is called if the sdk call throws an exception
        """
        mock_term.return_value = [TermStub(1, 'colgsas')]
        mock_ci.return_value = ValuesStub([CourseInstanceStub(course_instance_id=12345)])
        mock_sdk.side_effect = CanvasAPIError()
        process_terms('false', term_id=1)
        self.assertEqual(mock_logger.call_count, 1)
        args, kwargs = mock_logger.call_args
        self.assertGreaterEqual(args[0].find('CanvasAPIError'), 0)

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_multiple_terms(self, mock_term, mock_ci, mock_sdk):
        """
        Courses should be fetched for each term if multiple shoppable terms found
        """
        mock_term.return_value = [TermStub(1, 'colgsas'), TermStub(2, 'hds')]
        mock_ci.side_effect = [ValuesStub([CourseInstanceStub(course_instance_id=12345)]),
                               ValuesStub([CourseInstanceStub(course_instance_id=23456)])]
        process_terms('false')
        self.assertEqual(mock_sdk.call_count, 2)

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_multiple_courses(self, mock_term, mock_ci, mock_sdk):
        """
        SDK should be called once per course in courses_to_process
        """
        mock_term.return_value = [TermStub(1, 'colgsas')]
        mock_ci.return_value = ValuesStub([CourseInstanceStub(course_instance_id=12345),
                                           CourseInstanceStub(course_instance_id=23456)])
        process_terms('false', term_id=1)
        self.assertEqual(mock_sdk.call_count, 2)

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_no_course_id_found(self, mock_term, mock_ci, mock_sdk):
        """
        SDK should not be called if no course_id is found for a course
        """
        mock_term.return_value = [TermStub(1, 'colgsas')]
        mock_ci.return_value = ValuesStub([CourseInstanceStub(course_instance_id=None)])
        process_terms('false', term_id=1)
        self.assertEqual(mock_sdk.call_count, 0)
