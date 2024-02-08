import json
import logging
from datetime import datetime
from typing import Dict, List

import boto3
from botocore.exceptions import ClientError
from canvas_sdk import RequestContext

from coursemanager.models import Term
from django.conf import settings


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


def send_job_to_queueing_lambda(job_id: int, job_details_list: List, 
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

    max_batch_size = 2500 # To avoid exceeding the payload size limit for Lambda invocations.
    chunks = [job_details_list[x:x + max_batch_size] for x in range(0, len(job_details_list), max_batch_size)]
    for chunk in chunks:
        # Construct the job dict that will be sent to as a payload to queueing lambda.
        job_dict = {
            "job_id": job_id,
            "job_details_list": chunk, 
            "setting_to_be_modified": setting_to_be_modified,
            "desired_setting": desired_setting
        }

        # Invoke Lambda function
        response = lambda_client.invoke(
            FunctionName=QUEUEING_LAMBDA_NAME,
            InvocationType="Event",
            Payload=json.dumps(job_dict)
        )

        logger.info(f"Sent bulk course settings course IDs {job_id} to queueing Lambda {QUEUEING_LAMBDA_NAME}.",
                    extra={"response": response})
    
    return None
