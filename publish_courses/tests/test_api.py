# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from mock import (
    patch,
    Mock)

from django.conf import settings
import django_rq
from rest_framework import status
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError)
from rest_framework.test import (
    APIRequestFactory,
    APITestCase)

import publish_courses.api as api

QUEUE_NAME = settings.RQWORKER_QUEUE_NAME


class PublishCoursesAPIBaseTestCase(APITestCase):

    def setUp(self):
        super(PublishCoursesAPIBaseTestCase, self).setUp()
        self.queue = django_rq.get_queue(QUEUE_NAME)
        self.queue.empty()
        self.factory = APIRequestFactory()
        self.post_url = '/publish_courses/api/jobs'
        self.get_url = '/publish_courses/api/show_summary'

    def tearDown(self):
        super(PublishCoursesAPIBaseTestCase, self).tearDown()
        self.queue.empty()


class BulkPublishListCreateTestCase(PublishCoursesAPIBaseTestCase):

    def setUp(self):
        super(BulkPublishListCreateTestCase, self).setUp()
        self.request_data = {
            'account': 'abc',
            'term': '2015-1'
        }
        self.lti_data = {
            'custom_canvas_user_login_id': '1',
            'custom_canvas_account_sis_id': 'school:abc',
        }

    def _prep_request_and_post(self, data=None, lti_data=None):
        request_data = data if data is not None else self.request_data
        request_lti_data = lti_data if lti_data is not None else self.lti_data
        request_kwargs = {
            'content_type': 'application/json',
            'data': json.dumps(request_data),
        }
        self.request = self.factory.post(self.post_url, **request_kwargs)
        setattr(self.request, 'data', request_data)
        setattr(self.request, 'LTI', request_lti_data)
        bulk_publish = api.BulkPublishListCreate(request=self.request)
        return bulk_publish.create(self.request)

    def test_returns_success(self):
        """
        returns expected data and status code on success
        """
        response = self._prep_request_and_post()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['state'], 'queued')
        self.assertNotEquals(response.data['date_created'], None)

    def test_queues_job(self):
        """
        queues job on success
        """
        queue = django_rq.get_queue(QUEUE_NAME)
        self.assertEqual(queue.count, 0)

        response = self._prep_request_and_post()

        self.assertEqual(queue.count, 1)

    def test_invalid_account(self):
        """
        invalid account raises permission denied
        """
        data = {
            'account': 'someaccount',
            'term': '2015-1'
        }
        with self.assertRaises(PermissionDenied):
            self._prep_request_and_post(data)

    def test_missing_data(self):
        """
        Invalid/missing data raises Exception (REST framework converts that
        into a response with status code 400)
        """
        data = {}
        msg = 'account and term are required'
        with self.assertRaisesRegexp(DRFValidationError, msg):
            self._prep_request_and_post(data)

    def test_missing_lti_data(self):
        """
        Invalid/missing LTI data raises Exception (REST framework converts that
        into a response with status code 400)
        """
        lti_data = {}
        msg = 'Invalid LTI session'
        with self.assertRaisesRegexp(DRFValidationError, msg):
            self._prep_request_and_post(lti_data=lti_data)


@patch('publish_courses.api.BulkCourseSettingsOperation')
class SummaryListTestCase(PublishCoursesAPIBaseTestCase):

    def setUp(self):
        super(SummaryListTestCase, self).setUp()
        self.request_data = {
            'account_id': 'abc',
            'term_id': '2015-1'
        }

    def _prep_request_and_get(self, data=None):
        request_data = data if data is not None else self.request_data
        self.request = self.factory.get(self.get_url, data=request_data)
        self.request.query_params = request_data
        summary_list = api.SummaryList(request=self.request)
        return summary_list.list(self.request)

    def test_success_status(self, mock_op):
        """ returns expected status code on success """
        mock_op.return_value.get_canvas_courses.return_value = []
        response = self._prep_request_and_get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fetches_expected_courses(self, mock_op):
        """ gets courses based on expected op_config """
        expected_op_config = {
            'account': 'sis_account_id:school:{}'.format(
                self.request_data['account_id']),
            'term': 'sis_term_id:{}'.format(self.request_data['term_id'])
        }
        response = self._prep_request_and_get()
        self.assertEqual(mock_op.call_count, 1)
        args, kwargs = mock_op.call_args
        self.assertDictEqual(args[0], expected_op_config)

    @patch('publish_courses.api.SummaryList._get_courses')
    def test_shows_relevant_courses_only(self, mock_get_courses, *args):
        """ only shows published, unpublished, and completed courses """
        available = {'workflow_state': 'available'}
        unpublished = {'workflow_state': 'unpublished'}
        completed = {'workflow_state': 'completed'}
        other = {'workflow_state': 'other'}
        mock_get_courses.return_value = [
            available, unpublished, completed, other]
        # Note: `total` counts all courses, but we only expect category counts
        #       for these relevant workflow types
        expected_response_data = {
            'published': 1,
            'unpublished': 1,
            'concluded': 1,
            'total': 4}

        response = self._prep_request_and_get()

        self.assertDictEqual(response.data, expected_response_data)


class PublishCoursesAPILTIPermissionsTestCase(PublishCoursesAPIBaseTestCase):
    def setUp(self):
        super(PublishCoursesAPILTIPermissionsTestCase, self).setUp()
        # Even if we don't add IsAuthenticated to the APIView permission_classes
        # tuple, we need to do this because of the way DRF handles permissions
        # https://github.com/tomchristie/django-rest-framework/blob/3.5.3/rest_framework/views.py#L164
        self.user = Mock(is_authenticated=Mock(return_value=True))
        self.client.force_authenticate(user=self.user)

    def test_create_job_invalid_lti_session(self):
        """
        invalid lti session raises permission denied
        """
        request_kwargs = {
            'content_type': 'application/json',
            'data': json.dumps({}),
        }
        response = self.client.post(self.post_url, **request_kwargs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Invalid LTI session', response.data['detail'])

    def test_summary_list_invalid_lti_session(self):
        response = self.client.get(self.get_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Invalid LTI session', response.data['detail'])
