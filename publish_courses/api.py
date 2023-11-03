# -*- coding: utf-8 -*-

import logging
from typing import Dict, List, Optional

import boto3
import simplejson as json
from botocore.exceptions import ClientError
from django.conf import settings
from django.http import JsonResponse
from lti_school_permissions.decorators import lti_permission_required_check
from publish_courses.models import Job, JobDetails
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.serializers import JSONField, ModelSerializer
from ulid import ULID

from publish_courses import constants 
from async_operations.models import Process
from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation
from publish_courses.async_operations import bulk_publish_canvas_sites

logger = logging.getLogger(__name__)
PC_PERMISSION = settings.PERMISSION_PUBLISH_COURSES

# AWS configuration parameters from settings.
AWS_REGION_NAME = settings.BULK_PUBLISH_COURSES_SETTINGS['aws_region_name']
AWS_ACCESS_KEY_ID = settings.BULK_PUBLISH_COURSES_SETTINGS['aws_access_key_id']
AWS_SECRET_ACCESS_KEY = settings.BULK_PUBLISH_COURSES_SETTINGS['aws_secret_access_key']
QUEUE_NAME = settings.BULK_PUBLISH_COURSES_SETTINGS['job_queue_name']
VISIBILITY_TIMEOUT = settings.BULK_PUBLISH_COURSES_SETTINGS['visibility_timeout']

KW = {
    'region_name':  AWS_REGION_NAME,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}

try:
    # Create SQS client using the provided AWS configuration.
    SQS = boto3.client('sqs', **KW)

except ClientError as e:
    logger.error('Error configuring sqs client: %s', e, exc_info=True)
    raise
except Exception as e:
    logger.exception('Error configuring sqs')
    raise


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
    # process_name = 'publish_courses.async_operations.bulk_publish_canvas_sites'
    # queryset = Process.objects.filter(name=process_name).order_by('-date_created')
    serializer_class = ProcessSerializer
    # permission_classes = (LTIPermission,)
          
    def create(self, request, *args, **kwargs) -> Response:
        lti_session = getattr(self.request, 'LTI', {})
        audit_user_id = lti_session.get('custom_canvas_user_login_id')
        account_sis_id = lti_session.get('custom_canvas_account_sis_id')

        print("==========================================>>>", self.request.data)

        if not all((audit_user_id, account_sis_id)):
            raise DRFValidationError(
                'Invalid LTI session: custom_canvas_user_login_id and '
                'custom_canvas_account_sis_id required')

        account = self.request.data.get('account')
        term = self.request.data.get('term')
        if not all((account, term)):
            raise DRFValidationError('Both account and term are required')

        # For the moment, only the current school account can be operated on.
        if not account_sis_id[len('school:'):] == account:
            raise PermissionDenied

        selected_courses = self.request.data.get('course_list')
        account = f'sis_account_id:school:{account}'
        term = f'sis_term_id:{term}'

        print("==========================================>>>",
              "\naccount: ", account,
              "\nterm: ", term,
              "\naudit_user: ", audit_user_id,
              "\ncourse_list: ", selected_courses, "\n")

        # Define the list of messages to send.
        messages = []

        # Calculate total batches based on course count and batch size.
        course_id_batch_size = 50
        total_batches = (len(selected_courses) + course_id_batch_size - 1) // course_id_batch_size

        job_id = f'JOB-{str(ULID())}'  # Unique lexicographically sortable identifier.

        # Create job record in the database.
        job = Job.objects.create(job=job_id,
                                 school_id=account_sis_id[len('school:'):],
                                 created_by_user_id=audit_user_id,
                                 user_full_name= lti_session.get('lis_person_name_full'),
                                 job_details_total_count=len(selected_courses))
        job.save()

        # Split the course IDs into batches of 50 (also enumerate to get batch number for message_body var).
        for batch_number, i in enumerate(range(0, len(selected_courses), course_id_batch_size), start=1):
            course_batch = selected_courses[i:i + course_id_batch_size]
            print("==========================================>>>", ','.join(map(str, course_batch)))

            # Create the SQS message for this batch.
            message_id = f'MSG-{str(ULID())}'
            message_body = f'Course batch {batch_number}/{total_batches}. Job ID {job_id}. Message ID {message_id}.'
            message_attributes = {
                'job_id': {
                    'StringValue': str(job_id),
                    'DataType': 'String'
                },
                'account': {
                    'StringValue': str(account),
                    'DataType': 'String'
                },
                'term': {
                    'StringValue': str(term),
                    'DataType': 'String'
                },
                'audit_user': {
                    'StringValue': str(audit_user_id),
                    'DataType': 'String'
                },
                'course_list': {
                    'StringValue': ','.join(map(str, course_batch)),  # Course IDs as comma separated string.
                    'DataType': 'String'
                },
            }

            # Append the message to the list of messages for this batch.
            messages.append({
                'Id': message_id,
                'MessageBody': message_body,
                'MessageAttributes': message_attributes
            })    

        # self._send_sqs_message_batch(messages, sqs_msg_batch_size=10)
        print("==========================================>>>")

        # TODO: Response json data?
        return Response({}, status=status.HTTP_201_CREATED)
    
    def _send_sqs_message_batch(self, messages: List[Dict], sqs_msg_batch_size: int = 10) -> None:
        """
        Sends a batch of messages to an Amazon Simple Queue Service (SQS) queue.

        Note: As of 2023-11-02 you can use send_message_batch to send up to 10 messages to the specified queue.
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/send_message_batch.html
        """
        queue = SQS.get_queue_url(QueueName=QUEUE_NAME)['QueueUrl']

        for i in range(0, len(messages), sqs_msg_batch_size):
            batch = messages[i:i + sqs_msg_batch_size]
            response = SQS.send_message_batch(
                QueueUrl=queue,
                Entries=batch
            )

            context = {
                'batch': batch,
                'response': response
            }
            logger.debug(f'Job for bulk_publish_canvas_sites sent to SQS', extra=context)














































    def create_old(self, request, *args, **kwargs):
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
