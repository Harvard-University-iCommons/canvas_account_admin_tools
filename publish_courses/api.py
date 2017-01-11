# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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

from async.models import Process
from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation
from lti_permissions.decorators import lti_permission_required_check
from publish_courses.async_operations import bulk_publish_canvas_sites

logger = logging.getLogger(__name__)
PC_PERMISSION = settings.PERMISSION_PUBLISH_COURSES


class ProcessSerializer(ModelSerializer):
    details = JSONField()

    class Meta:
        model = Process
        exclude = ('name', 'source')


class LTIPermission(BasePermission):
    def has_permission(self, request, view):
        return lti_permission_required_check(request, PC_PERMISSION)


class SummaryList(ListAPIView):
    """
    Return counts of published courses using the GET parameters given
    :param term_id: The SIS term to count course instances for
    :param account_id: The SIS school ID to count course instances for
    :return: JSON response containing the course instance counts
    """
    permission_classes = (LTIPermission,)

    def list(self, request, *args, **kwargs):
        self.term_id = self.request.query_params.get("term_id")
        self.account_id = self.request.query_params.get("account_id")
        self.sis_term_id = 'sis_term_id:{}'.format(self.term_id)
        self.sis_account_id = 'sis_account_id:school:{}'.format(self.account_id)
        try:
            total_courses = self._get_courses()
            state_map = {
                'published': 'available',
                'unpublished': 'unpublished',
                'concluded': 'completed',
            }
            summary_counts_by_state = {'total': len(total_courses)}
            for k, v in state_map.items():
                summary_counts_by_state[k] = len(
                    [c for c in total_courses if c['workflow_state'] == v])
        except Exception as e:
            logger.exception(
                "Failed to get published courses summary for term_id={} and "
                "account_id={}".format(self.term_id, self.account_id))
            raise RuntimeError("There was a problem counting courses. ")

        return Response(summary_counts_by_state)

    def _get_courses(self):
        op_config = {
            'account': self.sis_account_id,
            'term': self.sis_term_id,
        }
        op = BulkCourseSettingsOperation(op_config)
        op.get_canvas_courses()
        return op.canvas_courses


class BulkPublishListCreate(ListCreateAPIView):
    process_name = 'publish_courses.async_operations.bulk_publish_canvas_sites'
    queryset = Process.objects.filter(name=process_name).order_by('-date_created')
    serializer_class = ProcessSerializer
    permission_classes = (LTIPermission,)

    def create(self, request, *args, **kwargs):
        audit_user_id = self.request.LTI['custom_canvas_user_login_id']
        account_sis_id = request.LTI['custom_canvas_account_sis_id']
        account = self.request.data.get('account')
        term = self.request.data.get('term')
        if not all((account, term)):
            raise DRFValidationError('Both account and term are required')

        # for the moment, only the current school account can be operated on
        if not account_sis_id[len('school:'):] == account:
            raise PermissionDenied

        process = Process.enqueue(
            bulk_publish_canvas_sites,
            'bulk_publish_canvas_sites',
            account='sis_account_id:school:{}'.format(account),
            term='sis_term_id:{}'.format(term),
            audit_user=audit_user_id)

        logger.debug('Enqueued Process job for bulk_publish_canvas_sites: '
                     '{}'.format(process))

        return Response(self.serializer_class(process).data,
                        status=status.HTTP_201_CREATED)
