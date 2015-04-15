import logging
import re
import time
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from canvas_sdk.methods import (accounts, courses)
from canvas_sdk.utils import get_all_list_data
from canvas_sdk.exceptions import CanvasAPIError
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import Term


SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-a', '--allow_access',
                    action='store',
                    dest='allow_access',
                    type='choice',
                    choices=['true', 'false'],
                    default='false',
                    help='allow access true or false'),

        make_option('-n', '--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=False,
                    help='do no harm'),
    )

    def handle(self, *args, **options):
        """
        TODO
        """

        allow_access = options.get('allow_access')
        print 'allow_access: %s' % allow_access
        dry_run = options.get('dry_run')
        verbosity = int(options.get('verbosity', 1))

        if verbosity > 1:
            logger.info('Verbosity set to %s' % verbosity)

        if dry_run:
            logger.info('Performing dry-run, no access will be set.')


        start_time = time.time()

        terms = Term.objects.filter(courses_public_to_auth_users=True)

        for term in terms:
            courses_to_exclude = term.courses_to_exclude.strip()
            course_list = re.findall(r"[\w']+", courses_to_exclude)
            course_set = set(map(int, course_list))
            account_id = 'sis_account_id:'+term.school_id
            courses_to_process = self.get_course_list(account_id, course_set)
            print 'courses_to_process: %s' % courses_to_process

            for course_id in courses_to_process:
                try:
                    '''
                    note that this is using the updated 'update_course' SDK method
                    '''
                    resp = courses.update_course(SDK_CONTEXT, course_id, account_id, course_is_public_to_auth_users=allow_access).json()
                    print 'id: %s, is_public_to_auth_users: %s' % (resp.get('id'), resp.get('is_public_to_auth_users'))
                except CanvasAPIError as api_error:
                    logger.error("CanvasAPIError in update_course call for course_id=%s in sub_account=%s. Exception=%s:"
                         % (course_id, account_id, api_error))

        end_time = time.time()
        total_time = end_time - start_time
        m, s = divmod(total_time, 60)
        h, m = divmod(m, 60)
        logger.info('command took %d:%02d:%02d seconds to run' % (h, m, s))


    def get_course_list(self, account_id, courses_to_exclude=None):
        '''
        given an account id, and a list of courses to exclude.
        get the list of courses to include.
        '''
        if not account_id:
            return None

        if not courses_to_exclude:
            courses_to_exclude = set()

        if isinstance(courses_to_exclude, list):
            courses_to_exclude = set(courses_to_exclude)

        if type(courses_to_exclude) is not set:
            raise TypeError('courses_to_exclude parameter must be of set or list type')

        course_ids_in_sub_account = set()
        courses_in_account = get_all_list_data(SDK_CONTEXT, accounts.list_active_courses_in_account, account_id, with_enrollments=True)
        for course in courses_in_account:
            canvas_course_id = course.get('id')
            if canvas_course_id:
                course_ids_in_sub_account.add(canvas_course_id)

        courses_to_update = course_ids_in_sub_account - courses_to_exclude

        return courses_to_update