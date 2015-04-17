from django.test import TestCase
from mock import patch, ANY, Mock
from term_tool.management.commands import set_allow_auth_users
from term_tool.management.commands.set_allow_auth_users import process_terms
import logging
from icommons_common.models import (Term, CourseInstance)
from mock import patch, call
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
    #     self.course_instance = CourseInstanceStub(123456)

    @patch('term_tool.management.commands.set_allow_auth_users.logger')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_invalid_term(self, mock_term, mock_logger):
        """
        Test that logger is called if no terms are returned
        """
        mock_term.return_value = []
        process_terms('true', term_id=123)
        mock_logger.assert_called()


    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.logger')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_valid_term(self, mock_term, mock_logger, mock_ci):
        """
        Test that CourseInstance.objects.filter is called if a term is found
        """
        term = TermStub(1, 'colgsas')
        mock_term.return_value = [term]
        process_terms('true', term_id=1)
        mock_ci.assert_called_with(sync_to_canvas=True, term=term.term_id, exclude_from_shopping=False)


    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.logger')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_valid_term_valid_set_true_course_sdk_call(self, mock_term, mock_logger, mock_ci, mock_sdk):
        """
        Test that the sdk is called with the correct params set to true
        """
        term = TermStub(1, 'colgsas')
        course = CourseInstanceStub(course_instance_id=12345)
        mock_term.return_value = [term]
        mock_ci.return_value = ValuesStub([course])
        process_terms('true', term_id=1)
        mock_sdk.assert_called_with(ANY, 'sis_course_id:%s' % course.course_instance_id, 'sis_account_id:colgsas', course_is_public_to_auth_users='true')

    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.logger')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_terms_valid_term_valid_set_false_course_sdk_call(self, mock_term, mock_logger, mock_ci, mock_sdk):
        """
        Test that the sdk is called with the correct params set to false
        """
        term = TermStub(1, 'colgsas')
        course = CourseInstanceStub(course_instance_id=12345)
        mock_term.return_value = [term]
        mock_ci.return_value = ValuesStub([course])
        process_terms('false', term_id=1)
        mock_sdk.assert_called_with(ANY, 'sis_course_id:%s' % course.course_instance_id, 'sis_account_id:colgsas', course_is_public_to_auth_users='false')


    @patch('term_tool.management.commands.set_allow_auth_users.courses.update_course')
    @patch('term_tool.management.commands.set_allow_auth_users.CourseInstance.objects.filter')
    @patch('term_tool.management.commands.set_allow_auth_users.logger')
    @patch('term_tool.management.commands.set_allow_auth_users.Term.objects.filter')
    def test_process_sdk_exception(self, mock_term, mock_logger, mock_ci, mock_sdk):
        """
        Test that logger is called if the sdk call throws an exception
        """
        term = TermStub(1, 'colgsas')
        course = CourseInstanceStub(course_instance_id=12345)
        mock_term.return_value = [term]
        mock_ci.return_value = ValuesStub([course])
        process_terms('false', term_id=1)
        mock_sdk.side_effect = CanvasAPIError()
        mock_logger.assert_called()
