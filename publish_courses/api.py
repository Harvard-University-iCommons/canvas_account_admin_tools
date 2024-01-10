# -*- coding: utf-8 -*-

import json
import logging
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError
from canvas_sdk import RequestContext
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
SQS_QUEUE_NAME = settings.BULK_PUBLISH_COURSES_SETTINGS['sqs_queue_name']
QUEUEING_LAMBDA_NAME = settings.BULK_PUBLISH_COURSES_SETTINGS['queueing_lambda_name']
VISIBILITY_TIMEOUT = settings.BULK_PUBLISH_COURSES_SETTINGS['visibility_timeout']

CREDENTIALS = {
    'region_name':  AWS_REGION_NAME,
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
}


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

        logger.info(f"{len(selected_courses)} selected courses for {account} and term {term}.",
                    extra={'account': account,
                           'term': term,
                           'audit_user': audit_user_id,
                           'course_list': selected_courses})

        if not selected_courses:
            courses = self._get_courses(account, term)
            # Filter unpublished courses.
            selected_courses = [cs_dict['id'] for cs_dict in courses if cs_dict['workflow_state'] == 'unpublished']

        # Save job and send to queueing lambda.
        job_dict = self.create_and_save_job(account_sis_id, self.request.data.get('term'),
                                            audit_user_id, audit_user_name, selected_courses)
        self.send_job_to_queueing_lambda(job_dict)

        logger.info(f'The bulk publish courses job creation for job ID {job_dict["job_id"]} is complete.')
        return Response(status=status.HTTP_201_CREATED)
    
    def _get_courses(self, account: str, term: str) -> List:
        """
        Returns a list of canvas courses for the given account and term.
        """
        logger.info(f"Retrieving all courses for {account} and term {term}.")

        op_config = {
            'account': account,
            'term': term
        }
        op = BulkCourseSettingsOperation(op_config)
        op.get_canvas_courses()

        logger.info(f"Retrieved {len(op.canvas_courses)} courses for {account} and term {term}.")
        return op.canvas_courses
    
    def create_and_save_job(self, account_sis_id: str, term: str, audit_user_id: int,
                            audit_user_name: str, selected_courses: List[int]) -> Dict:
        """
        Creates a job record, then creates job details then adds them to the database.
        Returns a dictionary containing job and job details (course IDs and PKs).
        """
        logger.info(f'Saving bulk publish courses job to database.')
        
        # Create job record in the database.
        job = Job.objects.create(school_id=account_sis_id[len('school:'):],
                                 term_id=term,
                                 created_by_user_id=audit_user_id,
                                 user_full_name=audit_user_name)
        job.save()
        logger.info(f'Bulk publish courses job saved to database. Job ID {job.pk}.')

        logger.info(f'Saving bulk publish courses job details for job ID {job.pk} to database.')
        # Create JobDetails objects to efficiently insert all objects into the database in a single query.
        job_details_objects = [JobDetails(parent_job=job, canvas_course_id=course_id) for course_id in selected_courses]
        just_created_job_objects = JobDetails.objects.bulk_create(job_details_objects)  # Bulk create JobDetails objects (save to database).

        # Construct the job dictionary (will be used by `send_job_to_queueing_lambda` func as payload).
        job_dict = {
            "job_id": job.pk,
            "course_list": [{"course_id": jo.canvas_course_id, "job_detail_id": jo.pk} for jo in just_created_job_objects]
        }

        logger.info(f'Details for the bulk publish courses job ID {job.pk} saved to database.')
        
        return job_dict 
        
    def send_job_to_queueing_lambda(self, job_dict: Dict) -> None:
        """
        Invokes SQS queueing Lambda with a payload of course ID list.
        This is a fire and forget method and will not wait for the Lambda to finish.
        """
        logger.info(f'Sending bulk publish courses job ID {job_dict["job_id"]} to queuing Lambda {QUEUEING_LAMBDA_NAME}.')
        
        try:
            # Create Lambda client
            lambda_client = boto3.client('lambda')
        except ClientError as e:
            logger.error(f'Error configuring Lambda client: {e}.', exc_info=True)
            raise
        except Exception as e:
            logger.exception('Error configuring Lambda client.')
            raise

        # Add queue name to payload data.
        job_dict["sqs_queue_name"] = SQS_QUEUE_NAME

        # Invoke Lambda function.
        response = lambda_client.invoke(
            FunctionName=QUEUEING_LAMBDA_NAME,
            InvocationType='Event',
            Payload=json.dumps(job_dict)
        )

        logger.info(f'Sent bulk publish courses job ID {job_dict["job_id"]} to queuing Lambda {QUEUEING_LAMBDA_NAME}.',
                    extra={'response': response})
        
        return None 
