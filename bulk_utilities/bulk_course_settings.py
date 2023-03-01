# -*- coding: utf-8 -*-

import logging
import re
import sys
import time

from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.accounts import list_active_courses_in_account
from canvas_sdk.methods.courses import get_single_course_courses, update_course
from canvas_sdk.utils import get_all_list_data
from django.conf import settings

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)

# The name of the course attribute differs from the argument that we need to
# pass to the update call, so we have this lookup table
ARG_ATTR_PAIRS = {
    'course_is_public': 'is_public',
    'course_is_public_to_auth_users': 'is_public_to_auth_users',
    'course_public_syllabus': 'public_syllabus',
    'course_event': 'workflow_state',
    'course_hide_final_grades': 'hide_final_grades'
}


class BulkCourseSettingsOperation(object):
    course_id_pattern = re.compile("^(sis_course_id:){0,1}\d+$")

    def __init__(self, options=None):
        self.SDK_CONTEXT = RequestContext(**SDK_SETTINGS)

        # todo: document options dict, or pull them out into individual params
        self.options = options if options else {}

        self.canvas_course_ids = set()
        self.canvas_courses = []
        self.total_count = 0
        self.update_courses = []
        self.update_count = 0
        self.failure_courses = []
        self.failure_count = 0
        self.skipped_courses = []
        self.skipped_count = 0

        self.metrics = {}

    def start_metric(self, metric_name, submetric_name=None):
        m = self.metrics.setdefault(metric_name, {})
        if submetric_name:
            m = m.setdefault(submetric_name, {})
        m['start'] = time.time()

    def end_metric(self, metric_name, submetric_name=None):
        m = self.metrics.setdefault(metric_name, {})
        if submetric_name:
            m = m.setdefault(submetric_name, {})
        m['end'] = time.time()
        if m.get('start', None) is not None:
            m['total'] = m['end'] - m['start']

    def _fetch_courses_from_id_list(self, id_list):
        for id in id_list:
            id = str(id)
            if self.course_id_pattern.match(id):
                id = id.strip()
                logger.info('fetching course {}'.format(id))
                try:
                    canvas_course_response = get_single_course_courses(
                        self.SDK_CONTEXT, id, ['permissions'])
                    self.canvas_course_ids.add(id)
                except CanvasAPIError as e:
                    logger.error('failed to find course {}. '
                                 'Maybe deleted?'.format(id))
                    continue
                canvas_course = canvas_course_response.json()
                self.canvas_courses.append(canvas_course)

    def get_canvas_courses(self):

        self.start_metric('get_canvas_courses')

        if self.options.get('list_file_name'):
            # open the list file and get all of the canvas courses
            list_file = open(self.options.get('list_file_name'), 'r')
            self._fetch_courses_from_id_list(list_file)
            list_file.close()

        # If a list of courses id's have been provided through the options dict,
        # Get the canvas courses from the given list.
        elif self.options.get('courses'):
            self._fetch_courses_from_id_list(self.options.get('courses'))

        # If a file or list of course id's have not been provided,
        # Get a list of all active canvas courses for the term and account id.
        else:
            try:
                self.canvas_courses = get_all_list_data(
                    self.SDK_CONTEXT,
                    list_active_courses_in_account,
                    account_id=self.options.get('account'),
                    enrollment_term_id=self.options.get('term'),
                    search_term=self.options.get('search_term'),
                    state=self.options.get('course_state'),
                )

            except Exception as e:
                message = 'Error listing active courses in account'
                if isinstance(e, CanvasAPIError):
                    message += ', SDK error details={}'.format(e)
                logger.exception(message)
                raise e

        self.end_metric('get_canvas_courses')

    def execute(self):
        # used in event of error to re-raise original exception after
        # logging output
        exc_during_execution = None
        exc_traceback = None

        logger.info('executing BulkCourseSettingsOperation with '
                    'options: %s' % self.options)

        self.start_metric('execute')

        try:
            self.get_canvas_courses()

            self.total_count = len(self.canvas_courses)

            logger.info('found %d courses' % self.total_count)

            for course in self.canvas_courses:
                self.check_and_update_course(course)
        except Exception as e:
            (_, _, exc_traceback) = sys.exc_info()
            exc_during_execution = e
            logger.exception('BulkCourseSettingsOperation.execute() '
                             'encountered an error, will attempt to log '
                             'operation summary before re-raising.')

        try:
            self.end_metric('execute')
            self._log_output()
        except Exception as e:
            # job completed execution, so consider it successful, even if there
            # are problems with output logging
            logger.exception('BulkCourseSettingsOperation.execute() unable to '
                             'complete logging of metrics and summary stats.')

        if exc_during_execution is not None:
            raise exc_during_execution.with_traceback(exc_traceback)

    def check_and_update_course(self, course):
        if self.options.get('skip') and \
                        str(course['id']) in self.options.get('skip'):
            logger.info('skipping course %s' % course['id'])
            self.skipped_courses.append(course['id'])
            self.skipped_count += 1
            return  # don't proceed, go to next course

        # check the settings, and change only if necessary
        update_args = self._build_update_args_for_course(course)
        logger.debug('update args for course {}: '
                     '{}'.format(course['id'], update_args))

        if not len(update_args):
            return  # nothing to do, go to next course

        self._log_update_args(course, update_args)

        self.update_course(course, update_args)
        self.update_courses.append(course['id'])
        self.update_count += 1

    def _log_update_args(self, course, update_args):
        logger.debug(
            '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' %
            (
                'DRY-RUN' if self.options.get('dry_run') else 'UPDATE',
                course['id'],
                course['name'],
                course.get('is_public', None),
                course.get('is_public_to_auth_users', None),
                course.get('public_syllabus', None),
                update_args.get('course_is_public', 'n/a'),
                update_args.get('course_is_public_to_auth_users', 'n/a'),
                update_args.get('course_public_syllabus', 'n/a'),
                update_args.get('course_event', 'n/a'),
                update_args.get('course_hide_final_grades', 'n/a')
            )
        )

        for update in update_args:
            logger.info(
                '%s\t%s\t%s\t%s\tnew=%s\t%s' %
                (
                    'DRY-RUN' if self.options.get('dry_run') else 'UPDATE',
                    course['id'],
                    course.get(ARG_ATTR_PAIRS[update], None),
                    update,
                    update_args.get(update, 'n/a'),
                    course['name'],
                )
            )

    def _build_update_args_for_course(self, course):
        update_args = {}

        if self.options.get('public') == 'true':
            if course['is_public'] is not True:
                update_args['course_is_public'] = 'true'
        elif self.options.get('public') == 'false':
            if course['is_public'] is True:
                update_args['course_is_public'] = 'false'

        if self.options.get('auth') == 'true':
            if course['is_public_to_auth_users'] is not True:
                update_args['course_is_public_to_auth_users'] = 'true'
        elif self.options.get('auth') == 'false':
            if course['is_public_to_auth_users'] is True:
                update_args['course_is_public_to_auth_users'] = 'false'

        if self.options.get('public_syllabus') == 'true':
            if course['public_syllabus'] is not True:
                update_args['course_public_syllabus'] = 'true'
        elif self.options.get('public_syllabus') == 'false':
            if course['public_syllabus'] is True:
                update_args['course_public_syllabus'] = 'false'

        if self.options.get('published') == 'true':
            if course['workflow_state'] == 'unpublished':
                update_args['course_event'] = 'offer'
        elif self.options.get('published') == 'false':
            if course['workflow_state'] == 'available':
                update_args['course_event'] = 'claim'

        if self.options.get('hide_final_grades') == 'true':
            if course['hide_final_grades'] is not True:
                update_args['course_hide_final_grades'] = 'true'
        elif self.options.get('hide_final_grades') == 'false':
            if course['hide_final_grades'] is True:
                update_args['course_hide_final_grades'] = 'false'

        return update_args

    def update_course(self, course, update_args):
        if self.options.get('dry_run'):
            return

        self.start_metric('update_course', course['id'])

        failure = False
        update_result = None

        try:
            update_result = update_course(
                self.SDK_CONTEXT, course['id'], **update_args)
        except CanvasAPIError as e:
            message = 'Error updating course {} via SDK with ' \
                      'parameters={}, SDK error ' \
                      'details={}'.format(course['id'], update_args, e)
            logger.exception(message)
            self.failure_count += 1
            failure = True

        if failure:
            try:
                self.failure_courses.append(course['id'])
            except (KeyError, NameError, TypeError) as e:
                logger.exception(
                    'Error recording course as failure: {}'.format(course))
        else:
            logger.debug('update result for course {}: {} - {}'.format(
                         course['id'], update_result, update_result.text))

        self.end_metric('update_course', course['id'])

    def _log_output(self):
        if self.options.get('dry_run'):
            logger.info(
                'DRY-RUN: would have updated %d/%d courses (%d skipped)'
                % (self.update_count, self.total_count, self.skipped_count))
        else:
            logger.info(
                'updated %d/%d courses (%d failures; %d skipped)'
                % (self.update_count, self.total_count, self.failure_count,
                   self.skipped_count))
            if self.update_count > 0:
                logger.info('updated courses: {}'.format(self.update_courses))
            if self.failure_count > 0:
                logger.info('failed courses: {}'.format(self.failure_courses))
            if self.skipped_count > 0:
                logger.info('skipped courses: {}'.format(self.skipped_courses))
        logger.info(self.summarize_metrics())

    def summarize_metrics(self):
        summary_metrics = ['execute', 'get_canvas_courses']
        summary = {}

        for m in summary_metrics:
            m_total = self.metrics.get(m, {}).get('total', 'unknown')
            m_total = round(m_total, 2) if isinstance(m_total, float) else 'unknown'
            summary[m] = {'total': m_total}

        course_totals = [m['total']
                         for c, m in list(self.metrics.get('update_course', {}).items())
                         if m.get('total') is not None]
        total_for_courses = sum(course_totals)
        average_for_courses = total_for_courses/(len(course_totals) or 1)
        min_for_courses = min(course_totals) if course_totals else 0
        max_for_courses = max(course_totals) if course_totals else 0

        summary['update_course'] = {
            'total': round(total_for_courses, 2),
            'average': round(average_for_courses, 2),
            'min': round(min_for_courses, 2),
            'max': round(max_for_courses, 2)}

        return summary

    def get_stats_dict(self):
        stats = {
            'total': self.total_count,
            'update': self.update_count,
            'failure': self.failure_count,
            'skipped': self.skipped_count}
        return stats
