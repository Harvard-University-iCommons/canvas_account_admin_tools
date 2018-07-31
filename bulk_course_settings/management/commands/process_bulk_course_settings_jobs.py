
import datetime
import logging
import signal
import sys
import time


from botocore.exceptions import ClientError

import boto3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bulk_course_settings.models import BulkCourseSettingsJob

logger = logging.getLogger(__name__)
queue_name = settings.BULK_COURSE_SETTINGS['job_queue_name']




class Command(BaseCommand):
    help = 'Process Bulk Course Setting Jobs from queue.'
    can_import_settings = True

    namespaces = {
        'http://icommons.harvard.edu/Schema': None,
    }

    # html_parser = HTMLParser()

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help="read the file but don't update the database")
        parser.add_argument('--school-id', help="the school ID is used to determine which queue to watch")
        parser.add_argument('--job-limit', help="shutdown after processing this many jobs", type=int)

    def handle(self, *args, **options):

        signal.signal(signal.SIGTERM, signal_handler)

        aws_region_name = settings.BULK_COURSE_SETTINGS['aws_region_name']
        aws_access_key_id = settings.BULK_COURSE_SETTINGS['aws_access_key_id']
        aws_secret_access_key = settings.BULK_COURSE_SETTINGS['aws_secret_access_key']

        kw = {'aws_access_key_id': aws_access_key_id,
              'aws_secret_access_key': aws_secret_access_key,
              'region_name': aws_region_name
              }

        try:
            self.sqs = boto3.resource('sqs', **kw)
        except Exception as e:
            logger.exception('Error configuring sqs')
            raise

        self.dry_run = options['dry_run']
        self.job_limit = options.get('job_limit')

        logger.info('starting a worker for queue %s with a job limit of %d', queue_name, self.job_limit)

        try:
            queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        except ClientError:
            logger.error('failed to get queue %s', queue_name)
            return False

        # loop indefinitely and get jobs from an SQS queue
        while True:
            # use long polling (wait up to 20 seconds) to reduce the number of receive_messages requests we make
            messages = queue.receive_messages(
                MaxNumberOfMessages=10,  # TODO: verify what value this should be set to
                MessageAttributeNames=['All'],
                AttributeNames=['All'],
                WaitTimeSeconds=20,
            )

            if messages:
                for message in messages:
                    if message:
                        self.handle_message(message)
            else:
                logger.info('no messages in queue %s', queue_name)
                time.sleep(40)

    def handle_message(self, message):
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
                bulk_course_setting_job.workflow_status = 'Queued'
                bulk_course_setting_job.save(update_fields=['workflow_status'])

                # TODO: Invoke method to process the individual job and populate the job details

                logger.info(" Message has been processed , deleting from sqs...")
                # delete the message from the queue once it is processed
                if self.dry_run:
                    # put the message back on the queue
                    message.change_visibility(VisibilityTimeout=0)
                else:
                    # delete the message from the queue so nobody else processes it
                    logger.debug(" deleting message....")
                    message.delete()

        except Exception as e:
            # put the message back on the queue
            logger.exception('Exception caught; re-queueing message %s', message.message_id)
            bulk_course_setting_job.workflow_status = 'Error'
            bulk_course_setting_job.save(update_fields=['workflow_status'])
            message.change_visibility(VisibilityTimeout=0)

        logger.info(" exiting handle_message for bulk_settings_id=" + bulk_settings_id)


class GracefulExit(Exception):
    logger.info('GracefulExit')


def signal_handler(signum, frame):
    raise GracefulExit()

