import logging
import time
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from canvas_sdk.methods import (courses)
from canvas_sdk.exceptions import CanvasAPIError
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import (Term, CourseInstance)


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

        terms = Term.objects.filter(shopping_active=True)

        for term in terms:
            logger.debug('term: %s' % term.display_name)
            account_id = 'sis_account_id:%s' % term.school_id

            courses_to_process = CourseInstance.objects.filter(term=term.term_id, exclude_from_shopping=False).values('course_instance_id', 'sync_to_canvas')

            for course in courses_to_process:
                sync_to_canvas = course.get('sync_to_canvas')
                if sync_to_canvas:
                    try:
                        '''
                        note that this is using the updated 'update_course' SDK method
                        '''
                        course_id = 'sis_course_id:%s' % course.get('course_instance_id')

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


