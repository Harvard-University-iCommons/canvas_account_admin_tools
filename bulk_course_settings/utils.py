import json
import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

from .models import BulkCourseSettingsJob

from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts_helper
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import Term


logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)
CACHE_KEY_CANVAS_SITE_TEMPLATES_BY_SCHOOL_ID = "canvas-site-templates-by-school-id_%s"

boto3.set_stream_logger('')
aws_region_name = settings.BULK_COURSE_SETTINGS['aws_region_name']
aws_access_key_id = settings.BULK_COURSE_SETTINGS['aws_access_key_id']
aws_secret_access_key = settings.BULK_COURSE_SETTINGS['aws_secret_access_key']


kw = {'aws_access_key_id': aws_access_key_id,
      'aws_secret_access_key': aws_secret_access_key,
      'region_name':  aws_region_name
}


try:
    sqs = boto3.resource('sqs', **kw)

except ClientError as e:
    logger.error('Error configuring sqs client: %s', e, exc_info=True)
    raise
except Exception as e:
    logger.exception('Error configuring sqs')
    raise


def get_school_data_for_user(canvas_user_id, school_sis_account_id=None):
    schools = []
    accounts = canvas_api_accounts_helper.get_school_accounts(
        canvas_user_id,
        canvas_api_accounts_helper.ACCOUNT_PERMISSION_MANAGE_COURSES
    )
    for account in accounts:
        sis_account_id = account['sis_account_id']
        school = {
            'id': account['sis_account_id'],
            'name': account['name']
        }
        if school_sis_account_id and school_sis_account_id == sis_account_id:
            return school
        else:
            schools.append(school)
    return schools


def get_school_data_for_sis_account_id(school_sis_account_id):
    school = None
    if not school_sis_account_id:
        return school
    school_sis_account_id = 'sis_account_id:{}'.format(school_sis_account_id)
    accounts = canvas_api_accounts_helper.get_all_sub_accounts_of_account(
        school_sis_account_id)
    for account in accounts:
        sis_account_id = account['sis_account_id']
        school = {
            'id': account['sis_account_id'],
            'name': account['name']
        }
        if school_sis_account_id == sis_account_id:
            return school
    return school


def get_term_data(term_id):
    term = Term.objects.get(term_id=int(term_id))
    return {
        'id': str(term.term_id),
        'name': term.display_name,
    }


def get_term_data_for_school(school_sis_account_id):
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
    now = timezone.now()
    current_term_id = None
    for term in query_set:
        # Picks the currently-active term with the earliest end date as the current term
        if term.start_date <= now < term.end_date:
            current_term_id = term.term_id
        terms.append({
            'id': str(term.term_id),
            'name': term.display_name
        })
    return terms


def queue_bulk_settings_job(queue_name, bulk_settings_id, school_id, term_id, setting_to_be_modified):
    logger.debug("queue_bulk_settings_job:  bulk_settings_id=%s, school_id=%s, term_id=%s, setting_to_be_modified=%s "
                 % (bulk_settings_id, school_id, term_id, setting_to_be_modified))
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    message = queue.send_message(
        MessageBody='_'.join(['msg_body', str(bulk_settings_id)]),
        MessageAttributes={

            'bulk_settings_id': {
                'StringValue': str(bulk_settings_id),
                'DataType': 'Number'
            },
            'school_id': {
                'StringValue': school_id,
                'DataType': 'String'
            },
            'term_id': {
                'StringValue': str(term_id),
                'DataType': 'Number'
            },
            'setting_to_be_modified': {
                'StringValue': setting_to_be_modified,
                'DataType': 'String'
            }
        }
    )
    logger.debug(json.dumps(message, indent=2))
    return message['MessageId']


def process_queue(queue_name):
    logger.debug(" in process_queue ....00")

    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)

        messages = queue.receive_messages(
            MaxNumberOfMessages=10,
            MessageAttributeNames=['All'],
            AttributeNames=['All'],
            WaitTimeSeconds=20,
        )

        if messages:
            logger.debug(len(messages))
            for message in messages:
                if message:
                    handle_message(message)
    except Exception as e:
        print e
        logger.error('failed to get queue %s', queue_name)
        return False


def handle_message(message):
        try:
            logger.info(message)
            m_attrs = message.attributes
            print "m_attrs=", m_attrs
            logger.info('message_attributes: %s', message.message_attributes)
            logger.info('body: %s', message.body)
            logger.info('message_id: %s', message.message_id)
            school_id = message.message_attributes['school_id']['StringValue']
            bulk_settings_id = message.message_attributes['bulk_settings_id']['StringValue']
            logger.info('received message %s for school %s', message.message_id, school_id)

            if bulk_settings_id:

                bulk_course_setting_job = BulkCourseSettingsJob.objects.get(id=bulk_settings_id)
                bulk_course_setting_job.workflow_status='Queued'
                bulk_course_setting_job.save(update_fields=['workflow_status'])

                # delete the message from the queue so nobody else processes it
                logger.info("deleting msg from queue.....")
                message.delete()

        except Exception as e:
            # put the message back on the queue
            logger.exception('Exception caught; re-queueing message %s', message.message_id)
            bulk_course_setting_job.workflow_status='Error'
            bulk_course_setting_job.save(update_fields=['workflow_status'])
            message.change_visibility(VisibilityTimeout=0)

        logger.info(" exiting handle_message for bulk_settings_id="+bulk_settings_id)