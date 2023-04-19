# -*- coding: utf-8 -*-

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError)
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView)
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.serializers import (
    JSONField,
    ModelSerializer)

from async_operations.models import Process
from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation
from lti_school_permissions.decorators import lti_permission_required_check
from publish_courses.async_operations import bulk_publish_canvas_sites
from django.http import JsonResponse
import simplejson as json
from django.conf import settings

logger = logging.getLogger(__name__)
PC_PERMISSION = settings.PERMISSION_PUBLISH_COURSES


class ProcessSerializer(ModelSerializer):
    details = JSONField()

    class Meta:
        model = Process
        exclude = ('name', 'source')


class LTIPermission(BasePermission):
    message = 'Invalid LTI session.'

    def has_permission(self, request, view):
        return lti_permission_required_check(request, PC_PERMISSION)


class CourseDetailList(ListAPIView):
    """
    Return a list of unpublished canvas courses and a summary of that list using the GET parameters given
    :param term_id: The SIS term to count course instances for
    :param account_id: The SIS school ID to count course instances for
    :return: JSON response containing a list of canvas courses for the given term/account and 
             a summary dictionary containing the counts of each workflow state of the courses.
    """
    permission_classes = (LTIPermission,)

    def list(self, request, *args, **kwargs):
        self.term_id = self.request.query_params.get("term_id")
        self.account_id = self.request.query_params.get("account_id")
        self.sis_term_id = 'sis_term_id:{}'.format(self.term_id)
        self.sis_account_id = 'sis_account_id:school:{}'.format(self.account_id)

        course_details = {
            'courses': [],
            'course_summary': {},
            'canvas_url': settings.CANVAS_URL
        }

        # The filtered list of courses that have the state of 'unpublished
        filtered_courses = []
        try:
            all_courses = self._get_courses()
            course_details['course_summary'] = self._get_summary(all_courses)

            for course in all_courses:
                if course['workflow_state'] == 'unpublished':
                    filtered_courses.append(course)

            course_details['courses'] = filtered_courses
        except Exception as e:
            logger.exception(
                "Failed to get unpublished courses for term_id={} and "
                "account_id={}".format(self.term_id, self.account_id))
            raise RuntimeError("There was a problem retrieving courses. ")

        return JsonResponse(course_details, safe=False)

    # Returns a list of canvas courses for the given account and term.
    def _get_courses(self):
        op_config = {
            'account': self.sis_account_id,
            'term': self.sis_term_id,
        }
        op = BulkCourseSettingsOperation(op_config)
        op.get_canvas_courses()
        return op.canvas_courses

    # Returns a dictionary summary of the given course list by their work state status.
    @staticmethod
    def _get_summary(course_list):
        state_map = {
            'published': 'available',
            'unpublished': 'unpublished',
            'concluded': 'completed',
        }
        summary_counts_by_state = {'total': len(course_list)}
        for k, v in list(state_map.items()):
            summary_counts_by_state[k] = len(
                [c for c in course_list if c['workflow_state'] == v])

        return summary_counts_by_state


class BulkPublishListCreate(ListCreateAPIView):
    process_name = 'publish_courses.async_operations.bulk_publish_canvas_sites'
    queryset = Process.objects.filter(name=process_name).order_by('-date_created')
    serializer_class = ProcessSerializer
    permission_classes = (LTIPermission,)

    def create(self, request, *args, **kwargs):
        lti_session = getattr(self.request, 'LTI', {})
        audit_user_id = lti_session.get('custom_canvas_user_login_id')
        account_sis_id = lti_session.get('custom_canvas_account_sis_id')
        if not all((audit_user_id, account_sis_id)):
            raise DRFValidationError(
                'Invalid LTI session: custom_canvas_user_login_id and '
                'custom_canvas_account_sis_id required')

        account = self.request.data.get('account')
        term = self.request.data.get('term')
        if not all((account, term)):
            raise DRFValidationError('Both account and term are required')

        # for the moment, only the current school account can be operated on
        if not account_sis_id[len('school:'):] == account:
            raise PermissionDenied

        selected_courses = self.request.data.get('course_list')

        process = Process.enqueue(
            bulk_publish_canvas_sites,
            settings.RQWORKER_QUEUE_NAME,
            account='sis_account_id:school:{}'.format(account),
            term='sis_term_id:{}'.format(term),
            audit_user=audit_user_id,
            course_list=selected_courses)

        logger.debug('Enqueued Process job for bulk_publish_canvas_sites: '
                     '{}'.format(process))

        return Response(self.serializer_class(process).data,
                        status=status.HTTP_201_CREATED)
