# -*- coding: utf-8 -*-

import json
import logging
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError
from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.accounts import list_active_courses_in_account
from canvas_sdk.utils import get_all_list_data
from django.conf import settings
from django.http import JsonResponse
from lti_school_permissions.decorators import lti_permission_required_check
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from ulid import ULID

from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation
from publish_courses.models import Job, JobDetails

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# Make sure the session_inactivity_expiration_time_secs key isn't in the settings dict.
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)

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

    def create(self, request, *args, **kwargs) -> Response:
        logger.info(f'Creating bulk publish courses job.')
        
        lti_session = getattr(self.request, 'LTI', {})
        audit_user_id = lti_session.get('custom_canvas_user_login_id')
        audit_user_name = lti_session.get('lis_person_name_full')
        account_sis_id = lti_session.get('custom_canvas_account_sis_id')

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
        print("==========================================>>>")

        canvas_courses = self.get_canvas_courses(account, term)
        if not selected_courses:
            selected_courses = canvas_courses

        # Unique lexicographically sortable identifier.
        job_id = f'JOB-{str(ULID())}'

        # Save job and send to sqs queue.
        self.create_and_save_job(
            job_id, account_sis_id, audit_user_id, audit_user_name, selected_courses, canvas_courses)
        messages = self.create_sqs_messages(
            job_id, account, term, audit_user_id, selected_courses)
        self.send_sqs_message_batch(messages, sqs_msg_batch_size=10)

        logger.info(f'Bulk publish courses job creation complete.')
        return Response(status=status.HTTP_201_CREATED)


    def get_canvas_courses(self, account: str, term: str) -> List[Dict]:
        """
        Fetches a list of Canvas courses for a specified account and term. 
        """
        logger.debug(f'Retrieving Canvas courses', extra={
                     'account': account, 'term': term})

        canvas_courses = []
        try:
            canvas_courses = get_all_list_data(
                SDK_CONTEXT,
                list_active_courses_in_account,
                account_id=account,
                enrollment_term_id=term,
                published=False,
            )
        except Exception as e:
            message = f'Error getting courses for account {account}'
            if isinstance(e, CanvasAPIError):
                message += ', SDK error details={}'.format(e)
            logger.exception(message)
            raise e

        return canvas_courses
    
    def create_and_save_job(self, job_id: str, account_sis_id: str, audit_user_id: int,
                            audit_user_name: str, selected_courses: List[int],
                            canvas_courses: List[Dict]) -> None:
        """
        Retrieves workflow states for selected courses, creates a job record,
        and job details then adds them to the database.
        """
        # Create job record in the database.
        job = Job.objects.create(job=job_id,
                                 school_id=account_sis_id[len('school:'):],
                                 created_by_user_id=audit_user_id,
                                 user_full_name=audit_user_name,
                                 job_details_total_count=len(selected_courses))
        job.save()

        logger.debug(f'Bulk publish courses job saved to database',
                     extra={'job_id': job_id})
        
        # Create dict workflow states for selected courses.
        workflow_states = {course['id']: course['workflow_state']
                           for course in canvas_courses if course['id'] in selected_courses}

        # Create job details records in the database.
        for course_id in selected_courses:
            # Get course workflow_state.
            workflow_state = workflow_states[course_id]

            job_details = JobDetails.objects.create(
                parent_job=job,
                canvas_course_id=course_id,
                prior_state=workflow_state
            )
            job_details.save()

        logger.debug(f'Details for the bulk publish courses job saved to database',
                     extra={'job_id': job_id})

    def create_sqs_messages(self, job_id: str, account: str, term: str, 
                            audit_user_id: int, selected_courses: List[int]) -> List[Dict]:
        """
        Creates SQS messages for a bulk publish courses job, with each message
        containing 50 course IDs."
        """
        messages = []

        # Calculate total course batches based on course count and batch size.
        course_id_batch_size = 50
        total_batches = (len(selected_courses) + course_id_batch_size - 1) // course_id_batch_size

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
                    # Course IDs as comma separated string.
                    'StringValue': ','.join(map(str, course_batch)),
                    'DataType': 'String'
                },
            }

            # Append the message to the list of messages for this batch.
            messages.append({
                'Id': message_id,
                'MessageBody': message_body,
                'MessageAttributes': message_attributes
            })

        return messages

    def send_sqs_message_batch(self, messages: List[Dict], sqs_msg_batch_size: int = 10) -> None:
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
            logger.debug(
                f'Bulk publish courses job sent to SQS', extra=context)
