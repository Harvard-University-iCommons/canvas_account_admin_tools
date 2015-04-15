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
    )

    def handle(self, *args, **options):
        """
        Get all the terms where shopping is active
        Then get all the courses in each term where exclude_from_shopping is False and sync_to_canvas is True
        These are the courses we want to set is_public_to_auth_users to True
        Cal the Canvas SDK to update each course
        Print out how long it took to run the command
        """

        allow_access = options.get('allow_access')
        start_time = time.time()

        terms = Term.objects.filter(shopping_active=True)
        for term in terms:
            account_id = 'sis_account_id:%s' % term.school_id
            courses_to_process = CourseInstance.objects.filter(term=term.term_id, exclude_from_shopping=False, sync_to_canvas=True).values('course_instance_id')
            for course in courses_to_process:
                try:
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


