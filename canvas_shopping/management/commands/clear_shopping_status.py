from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
#from django.db.models import Q
#from canvas_course_site_wizard.controller import (get_canvas_user_profile, send_email_helper, send_failure_email)
#from canvas_course_site_wizard.models import CanvasContentMigrationJob
#from canvas_course_site_wizard.controller import finalize_new_canvas_course
from canvas_sdk.methods import (courses, accounts, enrollments, users) 
from icommons_common.canvas_utils import (SessionInactivityExpirationRC, upload_csv_data, UnicodeCSVWriter)
from collections import OrderedDict
import logging
import io

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    
    args = '<shopping_role>'
    help = 'Removes course enrollments for the specified shopping role'
    
    def handle(self, *args, **options):
        
        if len(args) != 1:
            shopping_role = 'Harvard-Viewer'
        elif 'Harvard-Viewer' not in args or 'Shopper' not in args:
            self.stdout.write('\nInvalid argument, must be one of the following arguments: < Harvard-Viewer | Shopper >')
            self.stdout.write('Example: python manage.py clear_shopping_status Harvard-Viewer')
            self.stdout.write('If no argument is given, the shopping role will default to Harvard-Viewer.\n\n')
            exit()

        sub_account_list = accounts.get_sub_accounts_of_account(SDK_CONTEXT, settings.CANVAS_SHOPPING['ROOT_ACCOUNT'], recursive=True).json()
        sub_list = []
        for a in sub_account_list:
            sub_list.append(a['id'])

        enrollments_csv = io.BytesIO()
        swriter = UnicodeCSVWriter(enrollments_csv)
        enrollment_records = []
        swriter.writerow(['course_id', 'root_account', 'user_id', 'role', 'section_id', 'status'])
        
        for account_id in sub_list: 
            course_list = accounts.list_active_courses_in_account(SDK_CONTEXT, account_id, with_enrollments=True).json()
            for course in course_list:
                enrollment_list = enrollments.list_enrollments_courses(SDK_CONTEXT, course['id'], role=shopping_role).json()
                for enrollment in enrollment_list:
                    if shopping_role in enrollment['role']:
                        enrollment_records.append([str(course['sis_course_id']), '', str(enrollment['user']['sis_user_id']), enrollment['role'], course['sis_course_id'], 'deleted'])
                        self.stdout.write('%s,, %s, %s, %s, deleted' % (course['sis_course_id'], enrollment['user']['sis_user_id'], enrollment['role'], course['sis_course_id']))

        if len(enrollment_records) > 0:
            logger.info('+++ uploading %d enrollment records' % len(enrollment_records))
            swriter.writerows(enrollment_records)
            sis_import_id = upload_csv_data('enrollments', enrollments_csv.getvalue(), False, False)
            logger.info('+++ created enrollment import job %s' % sis_import_id)

            #archive_file = open('enrollments_%s.csv' % sis_import_id, 'w')
            #archive_file.write(enrollments_csv.getvalue())
            #archive_file.close()
        else:
            logger.info('+++ no records to process at this time')
            
