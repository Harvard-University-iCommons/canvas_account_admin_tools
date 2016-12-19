# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.core.management.base import BaseCommand

from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    # todo: update help text
    help = 'Finds all of the Canvas sites in a particular account and term ' \
           'and changes the settings to the values specified'
    can_import_settings = True

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--account', help='limit to a specific Canvas account; can be either a numeric Canvas account ID or an SIS account ID (e.g. sis_account_id:school:colgsas)')
        group.add_argument('--courses', nargs='*', help='limit to a specific set of Canvas course IDs separated by spaces')
        group.add_argument('--list', help='file containing list of Canvas course IDs to operate on')
        parser.add_argument('--term', help='limit to a specific Canvas term; can be either a numeric Canvas term ID or an SIS term ID (e.g. sis_term_id:2015-1)')
        parser.add_argument('--state', help='created|claimed|available|completed|deleted|all - If set, only return courses that are in the given state(s). By default, all states but "deleted" are returned.')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--public', choices=['true', 'false'], help='Set the "course is public" setting to this value')
        parser.add_argument('--auth', choices=['true', 'false'], help='Set the "course is public to authenticated users" setting to this value')
        parser.add_argument('--hide-final-grades', choices=['true', 'false'], help='Set the "Hide totals in student grades summary" setting to this value')
        parser.add_argument('--public-syllabus', choices=['true', 'false'], help='Set the "public syllabus" setting to this value')
        parser.add_argument('--published', choices=['true', 'false'], help='Set the published state to this value')
        parser.add_argument('--search', help='Limit to courses matching this search term (minimum three characters)')
        parser.add_argument('--skip', nargs='*', help='Canvas course IDs to skip')

    def handle(self, *args, **options):
        logger.info('bulk_course_settings Command running with options: %s' % options)
        op = BulkCourseSettingsOperation(options=options)
        op.execute()

