import logging
import signal

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand

import bulk_course_settings.utils as utils
from bulk_course_settings.models import BulkCourseSettingsJob
from icommons_common.models import Term

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process Bulk Course Setting Jobs from queue.'

    namespaces = {
        'http://icommons.harvard.edu/Schema': None,
    }

    def add_arguments(self, parser):
        parser.add_argument('--job-limit', help="Shutdown after processing this many jobs", type=int)

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, signal_handler)

        self.aws_region_name = settings.BULK_COURSE_SETTINGS['aws_region_name']
        self.aws_access_key_id = settings.BULK_COURSE_SETTINGS['aws_access_key_id']
        self.aws_secret_access_key = settings.BULK_COURSE_SETTINGS['aws_secret_access_key']
        self.queue_name = settings.BULK_COURSE_SETTINGS['job_queue_name']
        self.job_limit = options.get('job_limit')

        self.kw = {'aws_access_key_id': self.aws_access_key_id,
                   'aws_secret_access_key': self.aws_secret_access_key,
                   'region_name': self.aws_region_name
                   }

        try:
            self.sqs = boto3.resource('sqs', **self.kw)
        except Exception as e:
            logger.exception('Error configuring sqs')
            raise

        try:
            self.queue = self.sqs.get_queue_by_name(QueueName=self.queue_name)
        except ClientError:
            logger.error('Failed to get queue %s', self.queue_name)
            raise

        logger.info('Starting a worker for queue %s with a job limit of %d', self.queue_name, self.job_limit)

        # TODO uncomment the while loop and the sleep
        # Loop indefinitely and get jobs from an SQS queue
        # while True:
        # Use long polling (wait up to 20 seconds) to reduce the number of receive_messages requests we make
        messages = self.queue.receive_messages(
            MaxNumberOfMessages=10,  # TODO: verify what value this should be set to
            MessageAttributeNames=['All'],
            AttributeNames=['All'],
            WaitTimeSeconds=20,
        )

        if messages:
            for message in messages:
                self.handle_message(message)
        else:
            logger.info('No messages in queue %s', self.queue_name)
            # time.sleep(40)

    @staticmethod
    def handle_message(message):

        try:
            bulk_settings_id = message.message_attributes['bulk_settings_id']['StringValue']

            bulk_course_settings_job = BulkCourseSettingsJob.objects.get(id=bulk_settings_id)
            bulk_course_settings_job.workflow_status = 'IN_PROGRESS'
            bulk_course_settings_job.save()
        except BulkCourseSettingsJob.DoesNotExist:
            logger.exception('The bulk setting with a job id of {} does not exist'.format(bulk_settings_id))
            message.delete()

        if bulk_course_settings_job:
            try:
                # TODO
                # Check if this is a reversion, if so get the list of canvas ID's that need to be reverted

                # Else perform call without course id list

                term = Term.objects.get(term_id=bulk_course_settings_job.term_id)

                canvas_courses = utils.get_canvas_courses(
                    account_id='sis_account_id:school:{}'.format(bulk_course_settings_job.school_id),
                    term_id='sis_term_id:{}'.format(term.meta_term_id())
                )

                for course in canvas_courses:
                    utils.check_and_update_course(course, bulk_course_settings_job)

                logger.info(" Message has been processed , deleting from sqs...")
                message.delete()

                # TODO Make a check for the associated details and update the workflow_status appropriately

            except Exception as e:
                # Put the message back on the queue
                logger.exception('Exception caught; re-queueing message %s', message.message_id)
                bulk_course_settings_job.workflow_status = 'COMPLETED_FAILED'
                bulk_course_settings_job.save()
                message.change_visibility(VisibilityTimeout=0)


class GracefulExit(Exception):
    logger.info('GracefulExit')


def signal_handler(signum, frame):
    raise GracefulExit()

