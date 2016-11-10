import logging
import csv

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from icommons_common.utils import grouper
from icommons_common.models import CourseInstance

from canvas_course_site_wizard.models import BulkCanvasCourseCreationJob, CanvasSchoolTemplate


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Creates BulkCanvasCourseCreationJobs given a list of course instance IDs'
    option_list = BaseCommand.option_list + (
        make_option(
            '--csv',
            action='store',
            dest='csv_path',
            default=None,
            help='Provide the path to a csv file containing a list of course instance IDs'
        ),
        make_option(
            '--school',
            action='store',
            dest='school_id',
            default=None,
            help='Provide the school for this bulk job'
        ),
        make_option(
            '--term',
            action='store',
            dest='term_id',
            type=int,
            default=None,
            help='Provide the term for this bulk job'
        ),
        make_option(
            '--template',
            action='store',
            dest='template_id',
            type=int,
            default=None,
            help='Provide the template canvas course ID'
        ),
        make_option(
            '--huid',
            action='store',
            dest='creator_huid',
            default=None,
            help='Provide your HUID'
        ),
        make_option(
            '--batch',
            action='store',
            dest='batch_size',
            type=int,
            default=100,
            help='Provide the batch size of each bulk job (defaults to 100)'
        ),
    )

    def handle(self, *args, **options):
        try:
            csv_path = options['csv_path']
            school_id = options['school_id']
            term_id = options['term_id']
            template_id = options['template_id']
            creator_huid = options['creator_huid']
            batch_size = options['batch_size']
        except KeyError:
            raise CommandError(
                'You must provide all of the following options --csv, --school, --term --template.'
            )

        course_instance_ids = []
        try:
            with open(csv_path, 'rU') as csv_file:
                for row in csv.reader(csv_file):
                    course_instance_ids.append(int(row[0]))
        except (IOError, IndexError):
            raise CommandError("Failed to read csv file %s", csv_path)

        # Validate template
        try:
            CanvasSchoolTemplate.objects.get(template_id=template_id, school_id=school_id)
        except CanvasSchoolTemplate.DoesNotExist:
            raise CommandError(
                "Invalid template: Template Canvas course %d is not configured for school %s", template_id, school_id
            )

        # Validate course instance IDs
        invalid_course_instance_ids = []
        query_set = CourseInstance.objects.filter(
            course_instance_id__in=course_instance_ids
        ).values_list(
            'course_instance_id', 'term_id'
        )
        for ci_id, ci_term_id in query_set:
            if ci_term_id != term_id:
                course_instance_ids.remove(ci_id)
                invalid_course_instance_ids.append((ci_id, ci_term_id))

        logger.info("Creating %d Canvas courses in batches of %d", len(course_instance_ids), batch_size)
        for batch in [course_instance_ids[i:(i + batch_size)] for i in range(0, len(course_instance_ids), batch_size)]:
            bulk_job = BulkCanvasCourseCreationJob.objects.create_bulk_job(
                school_id=school_id,
                sis_term_id=term_id,
                template_canvas_course_id=template_id,
                created_by_user_id=creator_huid,
                course_instance_ids=batch
            )
            logger.info(
                "Created BulkCanvasCourseCreationJob %d which will create %d Canvas courses", bulk_job.id, len(batch)
            )

        if invalid_course_instance_ids:
            logger.error('Failed to create course creation jobs for invalid course instance IDs:')
            for ci_id, ci_term_id in invalid_course_instance_ids:
                logger.error("Course instance %d is from school %s and term %d", ci_id, ci_term_id)
