
import json
import boto3
import logging

from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


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


def queue_bulk_settings_job(queue_name, bulk_settings_id, school_id, term_id, setting_to_be_modified):
    logger.debug("queue_bulk_settings_job:  bulk_settings_id=%s, school_id=%s, term_id=%s, setting_to_be_modified=%s "
                 %(bulk_settings_id,school_id, term_id, setting_to_be_modified ))
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

