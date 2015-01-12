from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from canvas_sdk.methods import (courses, accounts, enrollments, users) 
from canvas_sdk.utils import get_all_list_data
from icommons_common.canvas_utils import (SessionInactivityExpirationRC, upload_csv_data, UnicodeCSVWriter)
from collections import OrderedDict
import logging
import io
import itertools
from optparse import make_option
from datetime import date

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
    make_option('--role',
        action='store',
        dest='shopping_role',
        default='Harvard-Viewer',
        help='Removes course enrollments for the specified shopping role'),
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

        shopping_role = options['shopping_role']
        if not verifyrole(shopping_role):
            self.printusage()
            exit()

        sub_account_list = get_all_list_data(SDK_CONTEXT, accounts.get_sub_accounts_of_account, settings.CANVAS_SHOPPING.get('ROOT_ACCOUNT', 1), recursive=True)

        sub_list = []
        for a in sub_account_list:
            sub_list.append(a['id'])

        today = date.today()

        enrollments_csv = io.BytesIO()
        swriter = UnicodeCSVWriter(enrollments_csv)
        enrollment_records = []
        swriter.writerow(['course_id', 'root_account', 'user_id', 'role', 'section_id', 'status'])
        for account_id in sorted(sub_list): 
            course_list = get_all_list_data(SDK_CONTEXT, accounts.list_active_courses_in_account, account_id, with_enrollments=True)
            for course in course_list:
                course_id = course.get('id', None)
                if course_id:
                    enrollment_list = get_all_list_data(SDK_CONTEXT, enrollments.list_enrollments_courses, course_id, role=['Harvard-Viewer', 'Shopper'])
                    for enrollment in enrollment_list:
                        enrollment_role = enrollment.get('role', None)
                        if shopping_role in enrollment_role:
                            # hotfix/TLT-487: if sis_user_id is unavailable for this user, skip
                            sis_section_id = enrollment.get('sis_section_id', None)
                            sis_user_id = str(enrollment['user'].get('sis_user_id', None))
                            if sis_user_id and sis_section_id:
                                created_at = enrollment.get('created_at', None)
                                updated_at = enrollment.get('updated_at', None)
                                last_activity_at = enrollment.get('last_activity_at', None)
                                sis_course_id = enrollment.get('sis_course_id', None)
                                total_activity_time = enrollment.get('total_activity_time', None)
                                logger.info('%s, %s, %s, %s, %s, %s, %s %s, %s' % (today, course_id, sis_course_id, sis_user_id, created_at, updated_at, last_activity_at, total_activity_time, enrollment_role))
                                enrollment_records.append([str(), '', sis_user_id, shopping_role, sis_section_id, 'deleted'])
        """
        Remove duplicate records from the list
        """
        enrollment_records.sort()
        enrollment_list = list(enrollment_records for enrollment_records, _ in itertools.groupby(enrollment_records))

        if len(enrollment_list) > 0:
            logger.info('+++ found %d records with role %s' % (len(enrollment_list), shopping_role))
            swriter.writerows(enrollment_list)
            sis_import_id = upload_csv_data('enrollments', enrollments_csv.getvalue(), False, False)
            logger.info('+++ created enrollment import job %s' % sis_import_id)
        else:
            logger.info('+++ no records to process at this time')

    def printusage(self):
        """
        display a usage message for this script.
        """
        self.stdout.write(' ')
        self.stdout.write('Invalid argument given!')
        self.stdout.write('Arguments must be one of the following: --role [Harvard-Viewer | Shopper]')
        self.stdout.write('    Example: python manage.py clear_shopping_status --role Harvard-Viewer')
        self.stdout.write('    If not argument is given it defaults to "Harvard-Viewer"')
        self.stdout.write(' ')

