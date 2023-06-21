import logging
import random
import string
from itertools import islice

from coursemanager.models import Course, CourseInstance, Term
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to help populate the COURSEMANAGER DB with test Courses and Course Instances.
    If course_id or term_id arguments are not provided, then a school argument must be provided to the command.
    """
    help = 'Creates course_instance records in the coursemanager DB to be used in bulk site creation testing'

    def add_arguments(self, parser):
        parser.add_argument('--term_id', help='Term to associate new Course Instances to')
        parser.add_argument('--course_id', help='Existing Course to associate new Course Instances to')
        parser.add_argument('--department_id', help='Department ID to associate a new Course to')
        parser.add_argument('--cg_id', help='Course Group ID to associate a new Course to')
        parser.add_argument('--school', help='Lowercase abbreviation of school to associate a new Course to')
        parser.add_argument('--amount', default=15, type=int, help='Amount of course instance records to create')

    def handle(self, *args, **options):
        if options.get('course-id'):
            course = Course.objects.get(course_id=options['course-id'])
        else:
            # String to be used for registrar code and registrar code display
            # Appends a random string so each execution of the command will have a unique course
            registrar_str = f"RegistrarCode-{''.join(random.choices(string.ascii_uppercase + string.digits, k=7))}"

            department_id = options.get('department-id')
            cg_id = options.get('cg-id')

            course = Course.objects.create(
                school_id=options['school'],
                registrar_code=registrar_str,
                source='mgmtcmd',
                registrar_code_display=registrar_str,
                department_id=department_id,
                course_group_id=cg_id
            )

        # If a term ID has been provided, get that Term object, otherwise get the most recent term for the given school
        if options.get('term-id'):
            term = Term.objects.get(term_id=options['term-id'])
        else:
            term = Term.objects.filter(school_id=options['school']).order_by('-term_id').first()

        print(f'Term ID:{term.term_id}, {term.display_name}')

        # Use bulk_create to efficiently insert CourseInstance records in batches of 500 up to the amount flag
        batch_size = 500
        objs = (CourseInstance(
            course=course,
            term=term,
            section='001',
            title=f'Test title {i}',
            short_title=f'Short title test {i}',
            sub_title=f'Sub title test {i}',
            source='mgmtcmd'
        ) for i in range(1, options['amount']+1))

        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            CourseInstance.objects.bulk_create(batch, batch_size)
