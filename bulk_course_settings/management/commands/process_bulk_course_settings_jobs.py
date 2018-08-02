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

        # WORKFLOW
        #
        # get message from the queue
            # get job record from the database
            # update the job status to IN_PROGRESS
            # find all of the courses matching job criteria
            #     for each course, create a job detail record in the NEW state
            #     get the current course settings and store in the detail record, change state to IN_PROGRESS
            #     determine if a change is necessary to match the target value
            #           if yes, make the API call to update the course in Canvas
            #               set is_modified to true
            #               save the new course attributes/settings
            #               if error, set state of detail record to FAILED (and continue processing courses)
            #           if no, set is_modified to false
            #     set workflow state of detail record to COMPLETED_SUCCESS
            # if all courses processed successfully, update job status to COMPLETED_SUCCESS
            # else update job status to COMPLETED_ERRORS
            # delete message from queue

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
        # get job record from the database
        # update the job status to IN_PROGRESS
        # find all of the courses matching job criteria
        #     for each course, create a job detail record in the NEW state
        #     get the current course settings and store in the detail record, change state to IN_PROGRESS
        #     determine if a change is necessary to match the target value
        #           if yes, make the API call to update the course in Canvas
        #               set is_modified to true
        #               save the new course attributes/settings
        #               if error, set state of detail record to FAILED (and continue processing courses)
        #           if no, set is_modified to false
        #     set workflow state of detail record to COMPLETED_SUCCESS
        # if all courses processed successfully, update job status to COMPLETED_SUCCESS
        # else update job status to COMPLETED_ERRORS
        # delete message from queue

        try:
            school_id = message.message_attributes['school_id']['StringValue']
            bulk_settings_id = message.message_attributes['bulk_settings_id']['StringValue']

            if bulk_settings_id:
                bulk_course_settings_job = BulkCourseSettingsJob.objects.get(id=bulk_settings_id)
                bulk_course_settings_job.workflow_status = 'IN_PROGRESS'
                bulk_course_settings_job.save()

                # TODO
                # Check if this is a reversion, if so get the list of canvas ID's that need to be reverted

                # Else perform call without course id list

                term = Term.objects.get(term_id=bulk_course_settings_job.term_id)

                canvas_courses = utils.get_canvas_courses(
                    account_id='sis_account_id:school:{}'.format(bulk_course_settings_job.school_id),
                    term_id='sis_term_id:{}'.format(term.meta_term_id())
                )

                for course in canvas_courses:
                    utils.check_and_update_course(course, bulk_course_settings_job.id)

                logger.info(" Message has been processed , deleting from sqs...")
                # delete the message from the queue so nobody else processes it
                logger.debug(" deleting message....")
                message.delete()

                # TODO Make a check for the associated details and update the workflow_status appropriately

        except Exception as e:
            # put the message back on the queue
            logger.exception('Exception caught; re-queueing message %s', message.message_id)
            # bulk_course_setting_job.workflow_status = 'Error'
            # bulk_course_setting_job.save(update_fields=['workflow_status'])
            message.change_visibility(VisibilityTimeout=0)

        logger.info(" exiting handle_message for bulk_settings_id=" + bulk_settings_id)


class GracefulExit(Exception):
    logger.info('GracefulExit')


def signal_handler(signum, frame):
    raise GracefulExit()

