# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import re

from django.conf import settings

from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.accounts import list_active_courses_in_account
from canvas_sdk.methods.courses import (
    get_single_course_courses,
    update_course)
from canvas_sdk.utils import get_all_list_data
from icommons_common.canvas_utils import SessionInactivityExpirationRC

logger = logging.getLogger(__name__)

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
    canvas_course_id_pattern = re.compile("^\d+$")

    def __init__(self, options=None):
        self.SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

        # todo: document options dict, or pull them out into individual params
        self.options = options if options else {}

        self.canvas_course_ids = set()
        self.canvas_courses = []
        self.total_count = 0
        self.update_count = 0
        self.failure_count = 0
        self.skipped_count = 0

    def _fetch_courses_from_id_list(self, id_list):
        for id in id_list:
            id = str(id)
            if self.canvas_course_id_pattern.match(id):
                id = id.strip()
                logger.info('fetching Canvas course {}'.format(id))
                try:
                    canvas_course_response = get_single_course_courses(
                        self.SDK_CONTEXT, id, ['permissions'])
                    self.canvas_course_ids.add(id)
                except Exception as e:
                    logger.error('failed to find Canvas course {}. '
                                 'Maybe deleted?'.format(id))
                    continue
                canvas_course = canvas_course_response.json()
                self.canvas_courses.append(canvas_course)

    def get_canvas_courses(self):
        if self.options.get('list_file_name'):
            # open the list file and get all of the canvas courses
            list_file = open(self.options.get('list_file_name'), 'r')
            self._fetch_courses_from_id_list(list_file)
            list_file.close()

        elif self.options.get('course_list'):
            self._fetch_courses_from_id_list(self.options.get('course_list'))

        else:
            try:
                self.canvas_courses = get_all_list_data(
                    self.SDK_CONTEXT,
                    list_active_courses_in_account,
                    account_id=self.options.get('account'),
                    enrollment_term_id=self.options.get('term'),
                    search_term=self.options.get('search_term'),
                    state=self.options.get('course_state'),
                    published=self.options.get('published'),
                )

            except Exception as e:
                message = 'Error listing active courses in account'
                if isinstance(e, CanvasAPIError):
                    message += ', SDK error details={}'.format(e)
                logger.exception(message)
                raise e

    def execute(self):
        logger.info('executing BulkCourseSettingsOperation with '
                    'options: %s' % self.options)

        self.get_canvas_courses()

        self.total_count = len(self.canvas_courses)

        logger.info('found %d courses' % self.total_count)

        for course in self.canvas_courses:
            self.check_and_update_course(course)

        self._log_output()

    def check_and_update_course(self, course):
        if self.options.get('skip') and \
                        str(course['id']) in self.options.get('skip'):
            logger.info('skipping course %s' % course['id'])
            self.skipped_count += 1
            return  # don't proceed, go to next course

        # check the settings, and change only if necessary
        update_args = self._build_update_args_for_course(course)
        logger.debug(update_args)

        if not len(update_args):
            return  # nothing to do, go to next course

        self._log_update_args(course, update_args)

        self.update_course(course, update_args)
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

        # do the update
        try:
            update_result = update_course(
                self.SDK_CONTEXT, course['id'], **update_args)
        except Exception as e:
            message = 'Error updating course {} via SDK with ' \
                      'parameters={}'.format(course['id'], update_args)
            if isinstance(e, CanvasAPIError):
                message += ', SDK error details={}'.format(e)
            logger.exception(message)
            self.failure_count += 1
        else:
            logger.debug(update_result)

    def _log_output(self):
        if self.options.get('dry_run'):
            logger.info(
                'DRY-RUN: would have updated %d/%d courses (skipped %d)'
                % (self.update_count, self.total_count, self.skipped_count))
        else:
            logger.info(
                'updated %d/%d courses (%d failures; skipped %d)'
                % (self.update_count, self.total_count, self.failure_count,
                   self.skipped_count))

    def get_stats_dict(self):
        stats = {
            'total': self.total_count,
            'update': self.update_count,
            'failure': self.failure_count,
            'skipped': self.skipped_count,
        }
        return stats
