import csv
import logging
import time

from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods import courses, sections
from canvas_sdk.utils import get_all_list_data
from coursemanager.models import CourseInstance, CourseSite, SiteMap
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)


class Command(BaseCommand):
	help = 'Process a CSV file containing a course_instance_id header and perform site deletion for each instance'

	def add_arguments(self, parser):
		parser.add_argument('--csv-file', type=str, help='Path to the CSV file')

	def handle(self, *args, **options):
		csv_file = options['csv_file']
		course_instance_ids = []

		with open(csv_file, 'r') as file:
			reader = csv.DictReader(file)
			course_instance_ids = [row['course_instance_id'] for row in reader]

		delete_courses(course_instance_ids)


def delete_courses(course_instance_ids):
	"""
	Get CourseInstance records in batches of 1000 (to avoid Oracle limit of 1000 records in a query)
	1. Set CourseInstance sync_to_canvas = 0
	2. Delete the course and any sections in Canvas
	3. Delete and CourseSite and SiteMap objects
	4. Set CourseInstance canvas_course_id = None
	"""

	logger.debug(f"PROCESSING {len(course_instance_ids)} course instance IDs")

	ts = int(time.time())

	max_chunk_size = 1000  # Max number of records to update at a time, to avoid going over the 1000 limit size for Oracle
	chunks = [course_instance_ids[x:x + max_chunk_size] for x in range(0, len(course_instance_ids), max_chunk_size)]
	for chunk in chunks:
		course_instances = CourseInstance.objects.filter(course_instance_id__in=chunk)
		course_instances.update(sync_to_canvas=0)

		for ci in course_instances:
			logger.debug(f"Processing course instance {ci.course_instance_id}")
			# Change the course/section SIS IDs and then delete the courses and sections
			try:
				canvas_course = courses.get_single_course_courses(SDK_CONTEXT, id=ci.canvas_course_id).json()
				canvas_sections = get_all_list_data(SDK_CONTEXT, sections.list_course_sections, ci.canvas_course_id)
				for s in canvas_sections:
					logger.info(f'Changing section {s["id"]} SIS ID to {s["sis_section_id"]}-deleted-{ts}')
					sections.edit_section(
						SDK_CONTEXT,
						id=s['id'],
						course_section_sis_section_id=f'{s["sis_section_id"]}-deleted-{ts}'
					)

				logger.info(f'Changing course {ci.canvas_course_id} SIS ID to {canvas_course["sis_course_id"]}-deleted-{ts} and then deleting the course')
				courses.update_course(SDK_CONTEXT, id=ci.canvas_course_id,
									  sis_course_id=f'{canvas_course["sis_course_id"]}-deleted-{ts}')
				logger.info(f'Deleting Canvas course {ci.canvas_course_id}')
				courses.conclude_course(SDK_CONTEXT, id=ci.canvas_course_id, event='delete')
			except CanvasAPIError as e:
				logger.exception(f'Failed to clean up Canvas course/sections for Canvas course ID {ci.canvas_course_id}')

			# Fetch course sites and site_map data
			try:
				logger.info(f'Deleting site_map and course_site records associated with course instance {ci.course_instance_id}')
				site_maps = SiteMap.objects.filter(course_instance=ci, map_type_id='official')
				for site_map in site_maps:
					if (settings.CANVAS_URL in site_map.course_site.external_id) and (str(ci.canvas_course_id) in site_map.course_site.external_id):
						logger.info(f'Deleting Canvas Sites associated with course : {site_map.course_site.external_id}')
						course_site_queryset = CourseSite.objects.filter(course_site_id=site_map.course_site_id)
						course_site_queryset.delete()
						logger.info(f'Deleting site map with the following details, site map ID:{site_map.site_map_id}, '
									'course instance ID:{site_map.course_instance.course_instance_id}, '
									'course site id:{site_map.course_site.course_site_id}, '
									'map type: {site_map.map_type}')
						site_map.delete()

			except Exception as e:
				logger.error(f'Error removing associated site_map/course_site from {ci.course_instance_id}, error: {e}')

		course_instances.update(canvas_course_id=None)

	logger.debug("DONE")
