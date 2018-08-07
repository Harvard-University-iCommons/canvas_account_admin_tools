import logging
import signal
import time

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand

import bulk_course_settings.utils as utils
from bulk_course_settings import constants
from bulk_course_settings.models import Job, Details
from icommons_common.models import Term
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process Bulk Course Setting Jobs from queue.'

    def add_arguments(self, parser):
        parser.add_argument('--job-limit', help="Shutdown after processing this many jobs", type=int)

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, signal_handler)

        self.job_limit = options.get('job_limit')

        try:
            self.queue = utils.SQS.get_queue_by_name(QueueName=utils.QUEUE_NAME)
        except ClientError:
            logger.error('Failed to get queue %s', utils.QUEUE_NAME)
            raise

        logger.info('Starting a worker for queue %s with a job limit of %d', utils.QUEUE_NAME, self.job_limit)

        job_count = 0
        # Loop indefinitely and get jobs from an SQS queue
        while True:
            # Check to see if we hit the job limit for this process, if so break out of the while loop
            if job_count >= self.job_limit:
                break
            else:
                # Use long polling (wait up to 20 seconds) to reduce the number of receive_messages requests we make
                messages = self.queue.receive_messages(
                    MaxNumberOfMessages=10,
                    MessageAttributeNames=['All'],
                    AttributeNames=['All'],
                    WaitTimeSeconds=20,
                )

                if messages:
                    for message in messages:
                        self.handle_message(message)

                        # Check to see if the job had any errors and update the workflow appropriately
                        bulk_settings_id = message.message_attributes['bulk_settings_id']['StringValue']
                        job = Job.objects.get(id=bulk_settings_id)
                        failed = Details.objects.filter(parent_job=bulk_settings_id, workflow_status=constants.FAILED)
                        if failed:
                            job.workflow_status = constants.COMPLETED_ERRORS
                        else:
                            job.workflow_status = constants.COMPLETED_SUCCESS
                        job.updated_at = datetime.now()
                        job.save()
                        job_count += 1
                else:
                    logger.info('No messages in queue {}'.format(utils.QUEUE_NAME))
                    time.sleep(40)

    @staticmethod
    def handle_message(message):
        try:
            bulk_settings_id = message.message_attributes['bulk_settings_id']['StringValue']

            job = Job.objects.get(id=bulk_settings_id)
            job.workflow_status = constants.IN_PROGRESS
            job.save()
        except Job.DoesNotExist:
            logger.exception('The bulk setting with a job id of {} does not exist'.format(bulk_settings_id))
            message.delete()

        if job:
            try:
                term = Term.objects.get(term_id=job.term_id)

                if job.related_job_id is not None:
                    # Check if this is a reversion, if so get the detail records from the related job and use
                    # the previous setting as the new desired setting to update the course.
                    # Exclude detail records that were skipped
                    related_job_details = Details.objects.\
                        filter(parent_job=job.related_job_id).\
                        exclude(workflow_status=constants.SKIPPED)
                    for detail in related_job_details:
                        utils.update_course(course={'id': detail.canvas_course_id, job.setting_to_be_modified: detail.current_setting_value},
                                            update_args={utils.API_MAPPING[job.setting_to_be_modified]: detail.current_setting_value},
                                            job=job)
                else:
                    # Otherwise get a list of active courses in the given account and given term
                    canvas_courses = utils.get_canvas_courses(
                        account_id='sis_account_id:school:{}'.format(job.school_id),
                        term_id='sis_term_id:{}'.format(term.meta_term_id()))

                    for course in canvas_courses:
                        utils.check_and_update_course(course, job)

                logger.info("Message has been processed , deleting from sqs...")
                message.delete()

            except Exception as e:
                # Put the message back on the queue
                logger.exception('Exception caught; re-queueing message %s', message.message_id)
                job.workflow_status = constants.COMPLETED_ERRORS
                job.save()
                message.change_visibility(VisibilityTimeout=0)


class GracefulExit(Exception):
    logger.info('GracefulExit')


def signal_handler(signum, frame):
    raise GracefulExit()
