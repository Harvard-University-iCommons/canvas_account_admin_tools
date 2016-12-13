from __future__ import unicode_literals
import json
from mock import ANY, call, Mock, patch

from django.test import Client, RequestFactory, TestCase

from canvas_site_creator.api import create_canvas_course_and_section
from canvas_sdk.exceptions import CanvasAPIError


@patch('django_auth_lti.decorators.is_allowed', new=Mock(return_value=True))
@patch('lti_permissions.decorators.is_allowed', new=Mock(return_value=True))
@patch('canvas_site_creator.api.logger.exception')
@patch('canvas_site_creator.api.create_course_section')
@patch('canvas_site_creator.api.create_new_course')
class APIHelperCreateCanvasCourseTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(APIHelperCreateCanvasCourseTest, cls).setUpClass()
        cls.client = Client()

    def setUp(self):
        super(APIHelperCreateCanvasCourseTest, self).setUp()
        self.post_data = {
            'course_code': 'ILE-test',
            'course_instance_id': 123456,
            'dept_id': 1,
            'school': 'gse',
            'section_id': '001',
            'short_title': 'test',
            'term_id': '0-99',  # Ongoing
            'title': 'test course'
        }
        self.url = '/lti_tools/canvas_site_creator/create_canvas_course'

    def _prep_request_and_post(self):
        request_kwargs = {
            'content_type': 'application/json',
            'data': json.dumps(self.post_data),
        }
        self.request = RequestFactory().post(self.url, **request_kwargs)
        # these values don't matter; the keys need to be present
        # for the authorization decorator patches to work
        self.request.LTI = {
            'custom_canvas_user_id': '1',
            'custom_canvas_account_sis_id': '1'
        }
        self.request.user = Mock(is_authenticated=Mock(return_value=True))

        return create_canvas_course_and_section(self.request)

    def test_course_sdk_error(self, mock_create_course, mock_create_section,
                              mock_logger_exception, *args, **kwargs):
        mock_create_course.side_effect = CanvasAPIError
        log_preamble = 'Error creating new course via SDK with request='
        log_sdk_status = 'SDK error details'

        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(mock_create_course.call_count, 1)
        self.assertEqual(mock_create_section.call_count, 0)
        self.assertEqual(mock_logger_exception.call_count, 1)
        log_message = mock_logger_exception.call_args[0][0]
        self.assertTrue(log_message.startswith(log_preamble))
        self.assertTrue(log_sdk_status in log_message)

    def test_course_non_sdk_error(self, mock_create_course, mock_create_section,
                                  mock_logger_exception, *args, **kwargs):
        mock_create_course.side_effect = ValueError  # e.g. JSON decoding error
        log_preamble = 'Error creating new course via SDK with request='
        log_sdk_status = 'SDK error details'

        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(mock_create_course.call_count, 1)
        self.assertEqual(mock_create_section.call_count, 0)
        self.assertEqual(mock_logger_exception.call_count, 1)
        log_message = mock_logger_exception.call_args[0][0]
        self.assertTrue(log_message.startswith(log_preamble))
        self.assertFalse(log_sdk_status in log_message)

    def test_missing_post_data(self, mock_create_course, mock_create_section,
                               mock_logger_exception, *args, **kwargs):
        del self.post_data['course_code']
        del self.post_data['short_title']

        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(mock_create_course.call_count, 0)
        self.assertEqual(mock_create_section.call_count, 0)
        self.assertEqual(mock_logger_exception.call_count, 1)
        self.assertEqual(mock_logger_exception.call_args, call(
            'Failed to extract canvas parameters from posted data; '
            'request body={}'.format(self.request.body)))

    def test_section_sdk_error(self, mock_create_course, mock_create_section,
                               mock_logger_exception, *args, **kwargs):
        mock_create_course.return_value.json.return_value = {'id': 1}
        mock_create_section.side_effect = CanvasAPIError
        log_preamble = ('Error creating section for new course via SDK with '
                        'request=')
        log_sdk_status = 'SDK error details'

        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(mock_create_course.call_count, 1)
        self.assertEqual(mock_create_section.call_count, 1)
        log_message = mock_logger_exception.call_args[0][0]
        self.assertTrue(log_message.startswith(log_preamble))
        self.assertTrue(log_sdk_status in log_message)

    def test_successful(self, mock_create_course, mock_create_section,
                        mock_logger_exception, *args, **kwargs):
        """
        Tests successful creation of canvas course and section based on
        expected parameters from POST. Course and section should be associated
        with short title (TLT-2493).
        """
        mock_create_course.return_value.json.return_value = {'id': 1}
        mock_create_section.return_value.json.return_value = {}

        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_create_course.call_count, 1)
        self.assertEqual(mock_create_course.call_args, call(
            request_ctx=ANY,
            account_id='sis_account_id:1',  # dept_id
            course_course_code='test',  # short_title
            course_name='test course',  # title
            course_sis_course_id=123456,  # course_instance_id
            course_term_id='sis_term_id:0-99'))  # term_id
        self.assertEqual(mock_create_section.call_count, 1)
        self.assertEqual(mock_create_section.call_args, call(
            request_ctx=ANY,
            course_id=1,  # mock_create_course.json()['id']
            course_section_name='GSE test 001',  # SCHOOL short_title section_id
            course_section_sis_section_id=123456))  # course_instance_id
        self.assertEqual(mock_logger_exception.call_count, 0)

    def test_successful_no_short_title(self, mock_create_course,
                                       mock_create_section,
                                       mock_logger_exception, *args, **kwargs):
        """
        Tests successful creation of canvas course and section based on
        expected parameters from POST, minus optional short_title parameter.
        Course and section should be associated with course code instead of
        short title (TLT-2493).
        """
        mock_create_course.return_value.json.return_value = {'id': 1}
        mock_create_section.return_value.json.return_value = {}
        # simulate omission of optional param
        self.post_data['short_title'] = ''

        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_create_course.call_count, 1)
        self.assertEqual(mock_create_course.call_args, call(
            request_ctx=ANY,
            account_id='sis_account_id:1',  # dept_id
            course_course_code='ILE-test',  # course_code
            course_name='test course',  # title
            course_sis_course_id=123456,  # course_instance_id
            course_term_id='sis_term_id:0-99'))  # term_id
        self.assertEqual(mock_create_section.call_count, 1)
        self.assertEqual(mock_create_section.call_args, call(
            request_ctx=ANY,
            course_id=1,  # mock_create_course.json()['id']
            course_section_name='GSE ILE-test 001',  # SCHOOL course_code section_id
            course_section_sis_section_id=123456))  # course_instance_id
        self.assertEqual(mock_logger_exception.call_count, 0)
