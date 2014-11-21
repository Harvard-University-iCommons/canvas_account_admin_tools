from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from canvas_sdk.methods import (courses, accounts, enrollments, users) 
from icommons_common.canvas_utils import (SessionInactivityExpirationRC, upload_csv_data, UnicodeCSVWriter)
from collections import OrderedDict
import logging
import io
from optparse import make_option

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

        Example of the canvas job url: <host>/api/v1/accounts/1/sis_imports/<job_id>
        """
        
        shopping_role = options['shopping_role']
        if not verifyrole(shopping_role):
            self.printusage()
            exit()

        sub_account_list = accounts.get_sub_accounts_of_account(SDK_CONTEXT, settings.CANVAS_SHOPPING.get('ROOT_ACCOUNT', 1), recursive=True).json()

        sub_list = []
        for a in sub_account_list:
            sub_list.append(a['id'])

        enrollments_csv = io.BytesIO()
        swriter = UnicodeCSVWriter(enrollments_csv)
        enrollment_records = []
        swriter.writerow(['course_id', 'root_account', 'user_id', 'role', 'section_id', 'status'])
        for account_id in sorted(sub_list): 
            course_list = accounts.list_active_courses_in_account(SDK_CONTEXT, account_id, with_enrollments=True).json()
            for course in course_list:
                enrollment_list = enrollments.list_enrollments_courses(SDK_CONTEXT, course['id'], role=shopping_role).json()
                for enrollment in enrollment_list:
                    if shopping_role in enrollment['role']:
                        # hotfix/TLT-487: if sis_user_id is unavailable for this user, skip
                        sis_user_id = str(enrollment['user'].get('sis_user_id', ''))
                        if sis_user_id:
                            enrollment_records.append([str(course['sis_course_id']), '', sis_user_id, enrollment['role'], course['sis_course_id'], 'deleted'])
                            logger.debug('%s,, %s, %s, %s, deleted' % (course['sis_course_id'], sis_user_id, enrollment['role'], course['sis_course_id']))

        if len(enrollment_records) > 0:
            logger.info('+++ found %d records with role %s' % (len(enrollment_records), shopping_role))
            swriter.writerows(enrollment_records)
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

