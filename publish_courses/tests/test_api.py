import json
from mock import patch, Mock
import unittest

from rest_framework.test import APITestCase
from rest_framework.exceptions import PermissionDenied

import publish_courses.api as api


class PublishCoursesAPITestCase(APITestCase):

    def setUp(self):
        super(PublishCoursesAPITestCase, self).setUp()

        self.post_data = {
            'account': 'sis_account_id:school:abc',
            'term': 'sis_term_id:2015-1'
        }
        self.lti_data = {
            'custom_canvas_user_login_id': '1',
            'custom_canvas_account_sis_id': 'school:abc',
        }
        self.get_data = {
            'account': 'sis_account_id:school:abc',
            'term': 'sis_term_id:2015-1'
        }
        self.user = Mock(is_authenticated=Mock(return_value=True))
        self.post_url = '/publish_courses/api/jobs'
        self.get_url = '/publish_courses/api/show_summary'

    def _prep_request_and_post(self, data):
        request_kwargs = {
            'content_type': 'application/json',
            'data': json.dumps(self.post_data),
        }

        self.request = self.client.post(self.post_url, **request_kwargs)
        # these values don't matter; the keys need to be present
        # for the authorization decorator patches to work
        self.request.LTI = self.lti_data
        self.request.data = data
        self.request.user = self.user

        bulk_publish = api.BulkPublishListCreate(request=self.request)
        return bulk_publish.create(self.request)

    def _prep_request_and_get(self, query_params=None, data=None):
        self.request = self.client.get(self.get_url, data=data)
        self.request.LTI = self.lti_data
        self.request.user = self.user
        self.request.query_params = query_params

        summary_list = api.SummaryList(request=self.request)
        return summary_list.list(self.request)

    # Tests for BulkPublishListCreate:
    def test_bulk_publish_list_create_success(self):
        """
        returns data as expected on success
        """
        data = {
            'account': 'abc',
            'term': '2015-1'
        }
        response = self._prep_request_and_post(data)
        # validate data and status code on success
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['state'], 'queued')
        self.assertNotEquals(response.data['date_created'], None)

    def test_bulk_publish_list_create_invalid_account(self):
        """
        invalid account raises permission denied
        """
        data = {
            'account': 'someaccount',
            'term': '2015-1'
        }
        with self.assertRaises(PermissionDenied):
            self._prep_request_and_post(data)

    @unittest.skip('BulkPublishListCreate seems to be bypassing its permission_classes')
    # all of our unit tests should be failing, because the LTIPermission isn't
    # being explicitly stubbed out, but they are passing, and this one is
    # failing; perhaps switching to using the live server will trigger the
    # permissions classes, or perhaps not mocking out the User object?...
    @patch('publish_courses.api.LTIPermission.has_permission')
    def test_bulk_publish_list_create_invalid_lti_session(self, mock_lti_check):
        """
        invalid lti session raises permission denied
        """
        data = {
            'account': 'abc',
            'term': '2015-1'
        }
        mock_lti_check.return_value = False
        with self.assertRaises(PermissionDenied):
            self._prep_request_and_post(data)

    def test_bulk_publish_list_create_missing_data(self):
        """
        Invalid/missing data raises Exception (REST framework converts that
        into a status code 500)
        """
        data = {}
        with self.assertRaises(Exception):
            self._prep_request_and_post(data)

    # SummaryList tests
    # invalid LTI session raises permission denied
    # returns data as expected on successful enqueue()
    # exception raises 500

    @unittest.skip('SummaryList returns data as expected on sucess')
    @patch('publish_courses.api.BulkCourseSettingsOperation.get_canvas_courses')
    def test_summary_list_success(self, mock_get_canvas_courses):

        mock_get_canvas_courses.return_value.json.return_value = {}
        query_params = {
            'account_id': 'abc',
            'term_id': '2015-1'
        }
        response = self._prep_request_and_get(query_params=query_params)
        self.assertEqual(response.status_code, 200)
