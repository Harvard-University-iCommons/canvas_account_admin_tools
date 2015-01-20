import logging
import io
import itertools
import time
from optparse import make_option
from datetime import date

from django.core.management.base import BaseCommand
from django.conf import settings
from canvas_sdk.methods import (accounts, enrollments)
from canvas_sdk.utils import get_all_list_data
from icommons_common.canvas_utils import (SessionInactivityExpirationRC, upload_csv_data, UnicodeCSVWriter)


SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

logger = logging.getLogger(__name__)


def verifyrole(role):
    """
    Verify that the role provided matches one of the allowed roles.
    """
    if 'Harvard-Viewer' == role:
        return True
    elif 'Shopper' == role:
        return True


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-r', '--role',
                    action='store',
                    dest='shopping_role',
                    type='choice',
                    choices=['Harvard-Viewer', 'Shopper'],
                    default='Harvard-Viewer',
                    help='the role to process'),

        make_option('-a', '--account_id',
                    action='store',
                    dest='main_account_id',
                    type='int',
                    default=settings.CANVAS_SHOPPING.get('ROOT_ACCOUNT', 1),
                    help='the account to process'),

        make_option('-n', '--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=False,
                    help='do no harm'),
    )

    def handle(self, *args, **options):
        """
        This command get the root account defined in settings.CANVAS_SHOPPING['ROOT_ACCOUNT'] and 
        users that to get a list of all the subaccounts. From there it gets a list of all the courses 
        in each account that contain at least one enrollment. FRom each course it will process the 
        courses enrollments looking for all records matching the desired shopping_role. It then build 
        csv file and calls canvas_utils.upload_csv_data. From there Canvas process each record in the csv
        file using the sis_import call. The upload_csv_data returns a progress job_id which can be checked
        to determine the state of the job.

        Note: if course is associated with multiple accounts, there will be duplicate records in the CSV.

        Example of the canvas job url: <host>/api/v1/accounts/1/sis_imports/<job_id>
        """

        shopping_role = options.get('shopping_role')
        main_account_id = options.get('main_account_id')
        dry_run = options.get('dry_run')
        verbosity = int(options.get('verbosity', 1))

        if verbosity > 1:
            logger.info('Verbosity set to %s' % verbosity)

        if dry_run:
            logger.info('Performing dry-run, no enrollments will be deleted.')

        logger.info('Removing role %s from account_id %s' % (shopping_role, main_account_id))

        start_time = time.time()

        sub_account_list = get_all_list_data(SDK_CONTEXT, accounts.get_sub_accounts_of_account, main_account_id,
                                             recursive=True)
        '''
            build a complete list of accounts including the passed in sub-account
        '''
        sub_list = [main_account_id]
        for a in sub_account_list:
            sub_list.append(a['id'])

        if verbosity > 1:
            logger.info('account list : %s' % set(sub_list))

        '''
            build a list of all active courses from the sub-account list above
        '''
        course_list = []
        course_id_list = []
        for account_id in set(sub_list):
            course_list = get_all_list_data(SDK_CONTEXT, accounts.list_active_courses_in_account, account_id)
            '''
            build a list of course id's from the course_list built above
            '''
            for course in course_list:
                course_id_list.append(course.get('id', None))

        course_id_set = set(course_id_list)

        if verbosity > 0:
            logger.info('course list : %s' % course_id_set)

        today = date.today()
        enrollments_csv = io.BytesIO()
        swriter = UnicodeCSVWriter(enrollments_csv)
        enrollment_records = []
        swriter.writerow(['course_id', 'root_account', 'user_id', 'role', 'section_id', 'status'])
        for course_id in course_id_list:
            if verbosity > 0:
                logger.info('course_id: %s' % course_id)
            if course_id:
                enrollment_list = get_all_list_data(SDK_CONTEXT, enrollments.list_enrollments_courses, course_id,
                                                    role=shopping_role)
                for enrollment in enrollment_list:
                    enrollment_role = enrollment.get('role', None)
                    if shopping_role in enrollment_role:
                        # hotfix/TLT-487: if sis_user_id is unavailable for this user, skip
                        sis_section_id = enrollment.get('sis_section_id', None)
                        sis_user_id = str(enrollment['user'].get('sis_user_id', None))

                        if verbosity > 1:
                            logger.info('sis_user_id: %s, sis_section_id: %s, enrollment_role: %s' % (sis_user_id, sis_section_id, enrollment_role))

                        if sis_user_id and sis_section_id:
                            created_at = enrollment.get('created_at', None)
                            updated_at = enrollment.get('updated_at', None)
                            last_activity_at = enrollment.get('last_activity_at', None)
                            sis_course_id = enrollment.get('sis_course_id', None)
                            total_activity_time = enrollment.get('total_activity_time', None)
                            logger.info('date=%s, canvas_course_id=%s, sis_course_id=%s, sis_user_id=%s, created_at=%s, updated_at=%s, last_activity_at=%s, total_activity_time=%s, enrollment_role=%s' % (
                                today, course_id, sis_course_id, sis_user_id, created_at, updated_at, last_activity_at,
                                total_activity_time, enrollment_role))
                            enrollment_records.append(
                                [str(), '', sis_user_id, shopping_role, sis_section_id, 'deleted'])
        """
        Remove duplicate records from the list
        """
        enrollment_records.sort()
        enrollment_list = list(enrollment_records for enrollment_records, _ in itertools.groupby(enrollment_records))

        if len(enrollment_list) > 0:
            logger.info('found %d records with role %s' % (len(enrollment_list), shopping_role))
            if not dry_run:
                swriter.writerows(enrollment_list)
                sis_import_id = upload_csv_data('enrollments', enrollments_csv.getvalue(), False, False)
                logger.info('created enrollment import job %s' % sis_import_id)
        else:
            logger.info('no records to process at this time')

        '''
        added some timing to track how long the command took to run
        '''
        end_time = time.time()
        total_time = end_time - start_time
        m, s = divmod(total_time, 60)
        h, m = divmod(m, 60)
        logger.info('command took %d:%02d:%02d seconds to run' % (h, m, s))

