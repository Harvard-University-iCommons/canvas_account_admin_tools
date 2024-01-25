import json
import logging
from datetime import datetime
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError
from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.accounts import list_active_courses_in_account
from canvas_sdk.methods.courses import update_course as sdk_update_course
from canvas_sdk.utils import get_all_list_data
from coursemanager.models import Term
from django.conf import settings

from bulk_course_settings import constants
from bulk_course_settings.models import Details

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)

AWS_REGION_NAME = settings.BULK_COURSE_SETTINGS['aws_region_name']
AWS_ACCESS_KEY_ID = settings.BULK_COURSE_SETTINGS['aws_access_key_id']
AWS_SECRET_ACCESS_KEY = settings.BULK_COURSE_SETTINGS['aws_secret_access_key']
QUEUEING_LAMBDA_NAME = settings.BULK_COURSE_SETTINGS['queueing_lambda_name']
VISIBILITY_TIMEOUT = settings.BULK_COURSE_SETTINGS['visibility_timeout']

KW = {
    'aws_access_key_id': AWS_ACCESS_KEY_ID,
    'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
    'region_name':  AWS_REGION_NAME
}

# The Canvas SDK requires a course_ prefix when making requests
# Use these 2 mappings to translate between the DB values and update arguments
API_MAPPING = {
    'is_public': 'course_is_public',
    'is_public_to_auth_users': 'course_is_public_to_auth_users',
    'public_syllabus': 'course_public_syllabus',
    'public_syllabus_to_auth': 'course_public_syllabus_to_auth'
}

REVERSE_API_MAPPING = {
    'course_is_public': 'is_public',
    'course_is_public_to_auth_users': 'is_public_to_auth_users',
    'course_public_syllabus': 'public_syllabus',
    'course_public_syllabus_to_auth': 'public_syllabus_to_auth'
}

try:
    SQS = boto3.resource('sqs', **KW)

except ClientError as e:
    logger.error('Error configuring sqs client: %s', e, exc_info=True)
    raise
except Exception as e:
    logger.exception('Error configuring sqs')
    raise


def get_term_data_for_school(school_sis_account_id):
    """Retrieves a list of active terms for the given school_sis_account_id"""
    school_id = school_sis_account_id.split(':')[1]
    year_floor = datetime.now().year - 5  # Limit term query to the past 5 years
    terms = []
    query_set = Term.objects.filter(
        school=school_id,
        active=1,
        calendar_year__gt=year_floor
    ).exclude(
        start_date__isnull=True
    ).exclude(
        end_date__isnull=True
    ).order_by(
        '-end_date', 'term_code__sort_order'
    )
    for term in query_set:
        terms.append({
            'id': str(term.term_id),
            'name': term.display_name
        })
    logger.info('Terms retrieved for account {}: {}'.format(school_sis_account_id, terms))
    return terms


def get_canvas_courses(account_id=None, term_id=None, search_term=None, state=None):
    """Returns a list of active courses for the given account and term"""
    try:
        canvas_courses = get_all_list_data(
            SDK_CONTEXT,
            list_active_courses_in_account,
            account_id=account_id,
            enrollment_term_id=term_id,
            search_term=search_term,
            state=state,
        )

        total_count = len(canvas_courses)
        logger.info('Found %d courses' % total_count)

    except Exception as e:
        message = 'Error listing active courses in account'
        if isinstance(e, CanvasAPIError):
            message += ', SDK error details={}'.format(e)
        logger.exception(message)
        raise e

    return canvas_courses


def check_and_update_course(course, job):
    """
    Checks if the given course requires an update using the value from the given Job.
    If it does not, create a skipped Detail entry for the given Job.
    """
    update_args = build_update_arg_for_course(course, job)
    logger.debug('Update args for course {}: {}'.format(course['id'], update_args))

    # Only update the course if the arg dict is not empty
    if len(update_args):
        logger.info('Course {} requires an update'.format(course['id']))
        update_course(course, update_args, job)
    else:
        logger.info('Course {} does not require an update, skipping...'.format(course['id']))
        Details.objects.create(
            parent_job=job,
            canvas_course_id=course['id'],
            current_setting_value=course[job.setting_to_be_modified],
            is_modified=True,
            prior_state=json.dumps(course),
            post_state='',
            workflow_status=constants.SKIPPED)
        # job.details_total_count += 1
        # job.details_skipped_count += 1
        job.save()


def build_update_arg_for_course(course, job):
    """
    Check if the given courses setting differs from the desired value of the given Job.
    If it does, make an entry in the update_args return dict with the API translated setting to be modified as the key
    and the job's desired value as its value.
    """
    update_args = {}

    setting_to_be_modified = job.setting_to_be_modified
    desired_value = job.desired_setting

    if course[setting_to_be_modified] is not True and desired_value == 'True':
        update_args[API_MAPPING[setting_to_be_modified]] = 'true'
    if course[setting_to_be_modified] is True and desired_value == 'False':
        update_args[API_MAPPING[setting_to_be_modified]] = 'false'

    return update_args


def update_course(course, update_args, job):
    """Uses the Canvas SDK to update the given course with the given update values."""
    try:
        logger.info('Updating course {} with update args {}'.format(course['id'], update_args))
        update_response = sdk_update_course(SDK_CONTEXT, course['id'], **update_args)
        logger.info('Successfully updated course {}'.format(course['id']))

        # update_job_detail_record(job_detail_id, status=constants.COMPLETED, post_state=json.dumps(update_response.json()))

    except Exception as e:
        message = 'Error updating course {} via SDK with parameters={}, SDK error details={}'\
            .format(course['id'], update_args, e)
        logger.exception(message)

    
    return update_response

        # update_job_detail_record(job_detail_id, status=constants.FAILED, post_state=json.dumps(update_response.json()))

# bring update_course and build_update_arg_for_course over to SAM app

def send_job_to_queueing_lambda(job_id: int, job_details_list: Dict, 
                                setting_to_be_modified: str, desired_setting: str) -> None:
    """
    Invokes SQS queueing Lambda with a payload of course ID list.
    This is a fire and forget method and will not wait for the Lambda to finish
    """
    logger.info(f'Sending bulk course settings {job_id} to queueing Lambda {QUEUEING_LAMBDA_NAME}')

    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda')
    except ClientError as e:
        logger.error(f'Error configuring Lambda client: {e}.', exc_info=True)
        raise
    except Exception as e:
        logger.exception('Error configuring Lambda client.')
        raise
    
    payload = {
        "job_id": job_id,
        "job_details_list": job_details_list, 
        "setting_to_be_modified": setting_to_be_modified,
        "desired_setting": desired_setting
    }

    # Invoke Lambda function
    response = lambda_client.invoke(
        FunctionName=QUEUEING_LAMBDA_NAME,
        InvocationType="Event",
        Payload=json.dumps(payload)
    )

    logger.info(f"Sent bulk course settings course IDs {job_id} to queueing Lambda {QUEUEING_LAMBDA_NAME}.",
                extra={"response": response})
    
    return None
