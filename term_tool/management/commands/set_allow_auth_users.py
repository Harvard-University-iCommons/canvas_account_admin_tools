import logging
import time
import json
from optparse import make_option
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from canvas_sdk.methods.courses import update_course
from canvas_sdk.exceptions import CanvasAPIError
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import (Term, CourseInstance)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-a', '--allow-access',
                    action='store',
                    dest='allow-access',
                    type='choice',
                    choices=['true', 'false'],
                    help='Required (true or false): whether or not to allow access to Canvas courses. '
                         'If true, sets is_public_to_auth_users flag in Canvas to true for courses in '
                         'shoppable terms (or the term specified in the sis-term-id parameter)'),
        make_option('-t', '--sis-term-id',
                    action='store',
                    dest='sis-term-id',
                    type='int',
                    default=None,
                    help='The SIS term ID to process (if you don\'t provide this parameter the process '
                         'will search through all shoppable terms for courses to update in Canvas)'),
        make_option('-d', '--dry-run',
                    action='store_true',
                    dest='dry-run',
                    default=False,
                    help='Use this setting if you want to see what courses would be affected without '
                         'actually updating them in Canvas'),
        make_option('-i', '--interval-in-minutes',
                    action='store',
                    dest='interval-in-minutes',
                    type='int',
                    default=None,
                    help='If provided, only course instances that have been updated in this time window '
                         'will be processed. INTERVAL-IN-MINUTES should be an integer. '
                         '(e.g. -i 15 will only process course instances updated in the last 15 minutes.) '
                         'You can use verbosity level 2 or higher to verify the exact window start time.'),
    )

    def handle(self, *args, **options):
        """
        Get all the terms where shopping is active
        Then get all the courses in each term where exclude_from_shopping is False
        and sync_to_canvas is True (and optionally only those changed within a certain time window)
        These are the courses we want to set is_public_to_auth_users to True
        Cal the Canvas SDK to update each course
        Print out how long it took to run the command
        """

        allow_access = options.get('allow-access')
        if not allow_access:
            raise CommandError('You must specify a value for the -a (--allow-access) parameter.')

        sis_term_id = options.get('sis-term-id')
        dry_run = options.get('dry-run')
        verbosity = int(options.get('verbosity', 1))
        interval_in_minutes = options.get('interval-in-minutes')

        start_time = datetime.now()

        process_terms(allow_access=allow_access, sis_term_id=sis_term_id, interval_in_minutes=interval_in_minutes,
                      dry_run=dry_run, verbosity=verbosity)

        logger.info('command took %s seconds to run' % str(datetime.now() - start_time)[:-7])


def process_terms(allow_access=False, sis_term_id=None, interval_in_minutes=None, dry_run=False, verbosity=1):

    courses_to_process = set()
    metrics = {}
    incremental_kwargs = {}

    if sis_term_id:
        terms = set(Term.objects.filter(term_id=sis_term_id, shopping_active=True).values_list('term_id', flat=True))
        if not terms:
            logger.info('Term %s not found or term does not have shopping enabled', sis_term_id)
            return
    else:
        terms = set(Term.objects.filter(shopping_active=True).values_list('term_id', flat=True))
        if not terms:
            logger.info('No terms have shopping enabled')
            return

    if interval_in_minutes:
        start_of_window = datetime.now() - timedelta(minutes=interval_in_minutes)
        logger.info('Performing incremental update based on last %s minutes (for courses updated since %s)'
                    % (interval_in_minutes, start_of_window.strftime('%c (%Y-%m-%d %H:%M:%S)')))
        # Note: incremental_kwargs may need to include other updated fields. We want to update Canvas if
        # CourseInstance's sync_to_canvas has changed to 1 or term ID has changed to a shoppable term.
        # If enrollment is updated along with term, it's not clear that COURSE_INST_LAST_UPDATED trigger
        # will actually change the value of LAST_UPDATED in COURSE_INSTANCE table. A naive possibility:
        #   Q(staff_last_updated__gte=start_of_window)
        #       | Q(guests_last_updated__gte=start_of_window)
        #       | Q(enrollment_last_updated__gte=start_of_window)
        #       | Q(last_updated__gte=start_of_window)
        incremental_kwargs['last_updated__gte'] = start_of_window

    for term in terms:
        start_time = time.time()
        courses_in_term = set(CourseInstance.objects
                              .filter(term=term, exclude_from_shopping=False, sync_to_canvas=True, **incremental_kwargs)
                              .values_list('course_instance_id', flat=True))
        courses_to_process |= courses_in_term
        if verbosity > 1:
            logger.debug('%s shoppable courses in CM term %s' % (len(courses_in_term), term))
            if verbosity > 2:
                logger.debug('(Courses: %s)' % courses_in_term)
        metrics.setdefault('get courses in SIS terms', []).append(time.time() - start_time)

    logger.info('%s shoppable Canvas courses in %s SIS terms' % (len(courses_to_process), len(terms)))
    if verbosity > 1:
        logger.debug('(Terms: %s)' % terms)
        if len(courses_to_process) > 0:
            logger.debug('(Courses: %s)' % courses_to_process)

    if not dry_run:
        for course_instance_id in courses_to_process:
            start_time = time.time()
            course_id = 'sis_course_id:%s' % course_instance_id
            try:
                resp = update_course(SDK_CONTEXT, course_id, course_is_public_to_auth_users=allow_access).json()
                if verbosity > 2:
                    logger.debug('update_course() response: %s' % json.dumps(resp, indent=2, sort_keys=True))
            except CanvasAPIError as api_error:
                logger.error("CanvasAPIError in update_course call for course_id=%s. Exception=%s"
                             % (course_id, api_error))
            metrics.setdefault('update courses', []).append(time.time() - start_time)

    if verbosity > 1:
        report_metrics(metrics)


def report_metrics(time_dict):
    for m_type, m_vals in sorted(time_dict.iteritems()):
        logger.info('Timer {}: average {:.2f} (high {:.2f} / low {:.2f}) for {:.0f} values (total {:.2f} seconds)'
                    .format(m_type, sum(m_vals)/len(m_vals), max(m_vals), min(m_vals), len(m_vals), sum(m_vals)))