from __future__ import unicode_literals

import json
import logging
import re
import sys
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.utils import timezone

from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.accounts import list_active_courses_in_account
from canvas_sdk.methods.courses import (
    get_single_course_courses,
    update_course)
from canvas_sdk.utils import get_all_list_data
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







# The name of the course attribute differs from the argument that we need to
# pass to the update call, so we have this lookup table
ARG_ATTR_PAIRS = {
    'course_is_public': 'is_public',
    'course_is_public_to_auth_users': 'is_public_to_auth_users',
    'course_public_syllabus': 'public_syllabus',
    'course_event': 'workflow_state',
    'course_hide_final_grades': 'hide_final_grades'
}


course_id_pattern = re.compile("^(sis_course_id:){0,1}\d+$")


def fetch_courses_from_id_list(course_id_list):
    canvas_course_ids = []
    canvas_courses = []

    for course_id in course_id_list:
        course_id = str(course_id)
        if course_id_pattern.match(course_id):
            course_id = course_id.strip()
            logger.info('fetching course {}'.format(id))
            try:
                canvas_course_response = get_single_course_courses(
                    SDK_CONTEXT, course_id, ['permissions'])
                canvas_course_ids.add(course_id)
            except CanvasAPIError as e:
                logger.error('failed to find course {}. '
                             'Maybe deleted?'.format(course_id))
                # TODO Create detail with a failed status
                continue
            canvas_course = canvas_course_response.json()
            canvas_courses.append(canvas_course)
    return canvas_courses


def get_canvas_courses(course_id_list, account_id=None, term_id=None, search_term=None, state=None):

    # If a list of courses id's have been provided through the options dict,
    # Get the canvas courses from the given list.
    #  TODO Will need to be done in the function that calls this but create a course_id_list based off of the
    # job details that require an update (or if we are including skips, those as well)
    if course_id_list:
        canvas_courses = fetch_courses_from_id_list(course_id_list)

    # If a file or list of course id's have not been provided,
    # Get a list of all active canvas courses for the term and account id.
    else:
        try:
            canvas_courses = get_all_list_data(
                SDK_CONTEXT,
                list_active_courses_in_account,
                account_id=account_id,
                enrollment_term_id=term_id,
                search_term=search_term,
                state=state,
            )

        except Exception as e:
            message = 'Error listing active courses in account'
            if isinstance(e, CanvasAPIError):
                message += ', SDK error details={}'.format(e)
            logger.exception(message)
            raise e

    return canvas_courses


def execute():
    # used in event of error to re-raise original exception after
    # logging output
    exc_during_execution = None
    exc_traceback = None

    try:
        canvas_courses = get_canvas_courses()

        total_count = len(canvas_courses)

        logger.info('found %d courses' % total_count)

        for course in canvas_courses:
            check_and_update_course(course)
    except Exception as e:
        (_, _, exc_traceback) = sys.exc_info()
        exc_during_execution = e
        logger.exception('BulkCourseSettingsOperation.execute() '
                         'encountered an error, will attempt to log '
                         'operation summary before re-raising.')

    try:
        # end_metric('execute')
        # _log_output()
        pass
    except Exception as e:
        # job completed execution, so consider it successful, even if there
        # are problems with output logging
        logger.exception('BulkCourseSettingsOperation.execute() unable to '
                         'complete logging of metrics and summary stats.')

    if exc_during_execution is not None:
        raise exc_during_execution, None, exc_traceback


def check_and_update_course(course):
    # TODO Check workflow state of detail?
    # if options.get('skip') and \
    #                 str(course['id']) in options.get('skip'):
    #     logger.info('skipping course %s' % course['id'])
    #     skipped_courses.append(course['id'])
    #     return  # don't proceed, go to next course

    # check the settings, and change only if necessary
    update_args = build_update_arg_for_course(course)
    logger.debug('update args for course {}: '
                 '{}'.format(course['id'], update_args))

    if not len(update_args):
        return  # nothing to do, go to next course


    update_course(course, update_args)
    # update_courses.append(course['id'])
    # TODO create detail with success


def build_update_arg_for_course(course, desired_setting, value):
    # Since we only update one setting at a time, check if the given courses setting differs from the value we want
    # and if it does make it an update argument.
    update_args = {}

    if course[desired_setting] is not True and value is True:
        update_args[desired_setting] = 'true'
    if course[desired_setting] is True and value is False:
        update_args[desired_setting] = 'false'

    return update_args


def update_course(course, update_args):
    failure = False
    update_result = None

    try:
        update_result = update_course(
            SDK_CONTEXT, course['id'], **update_args)
    except CanvasAPIError as e:
        message = 'Error updating course {} via SDK with ' \
                  'parameters={}, SDK error ' \
                  'details={}'.format(course['id'], update_args, e)
        logger.exception(message)
        failure = True

    if failure:
        try:
            # failure_courses.append(course['id'])
            # TODO Create detail with failed status
            pass
        except (KeyError, NameError, TypeError) as e:
            logger.exception(
                'Error recording course as failure: {}'.format(course))
    else:
        logger.debug('update result for course {}: {} - {}'.format(
                     course['id'], update_result, update_result.text))




