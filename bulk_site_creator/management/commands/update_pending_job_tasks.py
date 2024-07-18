import logging

import boto3
from boto3.dynamodb.conditions import Key
from coursemanager.models import CourseInstance
from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
import datetime

logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")
table_name = settings.BULK_COURSE_CREATION.get("site_creator_dynamo_table_name")


class Command(BaseCommand):
	help = ('Updates bulk site creator DynamoDB records with workflow_state set to pending to fail '
	        'and update CourseInstance bulk_processing flag to false')

	def add_arguments(self, parser: CommandParser) -> None:
		parser.add_argument('--job-id', type=str, required=True, help='The Job ID (SK for main record PK for tasks) value in Dynamo; eg: JOB#12345')
		parser.add_argument('--school-id', type=str, required=True, help='The School ID that is the primary job PK value in Dynamo; eg: SCHOOL#COLGSAS')

	def handle(self, *args, **options):
		job_id = options['job_id']
		school_id = options['school_id']
		table = dynamodb.Table(table_name)
		course_instance_id_list = []

		query_params = {
			'KeyConditionExpression': Key('pk').eq(job_id),
			'FilterExpression': 'workflow_state = :state',
			'ExpressionAttributeValues': {':state': 'pending'}
		}

		query_items = query_dynamo(query_params)

		for item in query_items:
			sk = item['sk']
			course_instance_id_list.append(item['course_instance_id'])

			logger.info(f'Updating task {sk} for job {job_id} with workflow_state from pending to fail')
			now = datetime.datetime.now()
			table.update_item(
				Key={'pk': job_id, 'sk': sk},
				UpdateExpression='SET workflow_state = :new_state, updated_at = :current_time',
				ExpressionAttributeValues={':new_state': 'fail', ':current_time': now}
			)

		max_chunk_size = 1000  # Max number of records to update at a time, to avoid going over the 1000 limit size for Oracle
		chunks = [course_instance_id_list[x:x + max_chunk_size] for x in range(0, len(course_instance_id_list), max_chunk_size)]
		for chunk in chunks:
			logger.info(f'Updating CI records bulk_processing flag to 0 for job {job_id}, ci_ids: {chunk}')
			CourseInstance.objects.filter(course_instance_id__in=chunk).update(bulk_processing=0)

		# Generate summary and update main Job record
		task_succeeded = 0
		task_failed = 0

		query_params = {
			'KeyConditionExpression': Key('pk').eq(job_id),
			'Select': 'SPECIFIC_ATTRIBUTES',
			'ProjectionExpression': 'workflow_state'  # Only retrieve the workflow_state attribute from the task
		}

		query_items = query_dynamo(query_params)

		for item in query_items:
			if item['workflow_state'] == 'complete':
				task_succeeded += 1
			elif item['workflow_state'] == 'fail':
				task_failed += 1

		task_total = task_succeeded + task_failed

		logger.info(f'Updating summary for job: {job_id} with the following: Total tasks: {task_total}, Succeeded: {task_succeeded}, Failed: {task_failed}')

		now = str(datetime.datetime.now())
		table.update_item(
			Key={'pk': school_id, 'sk': job_id},
			UpdateExpression='SET workflow_state = :complete, updated_at = :current_time, task_total = :task_total, task_failed = :task_failed, task_succeeded = :task_succeeded',
			ExpressionAttributeValues={':complete': 'complete', ':current_time': now, ':task_total': task_total, ':task_failed': task_failed, ':task_succeeded': task_succeeded},
		)

		logger.info(f'Successfully updated records for job {job_id} with workflow_state from to pending to fail')


# From TutorBot Admin Project
def query_dynamo(query_params, limit=0, sort_descending=True):
	"""
	Queries the DynamoDB with the given query_params
	Returns the Items of the resulting query, up to the limit if present, with the created_at field formatted
	Sorted DESC by default unless sort_descending is set to False
	"""
	table = dynamodb.Table(table_name)

	# By default, the sort order is ascending. To reverse the order, set the ScanIndexForward parameter to False
	# Give priority to the value of ScanIndexForward if it is already in the query params
	if "ScanIndexForward" not in query_params and sort_descending:
		query_params["ScanIndexForward"] = False

	# Check if a Limit was defined in the query params and give priority over the function parameter
	# Otherwise if the limit param was used, set the query param for that value
	if "Limit" in query_params:
		limit = query_params["Limit"]
	elif limit:
		query_params["Limit"] = limit

	logger.info(f"Querying the Dynamo table: {table_name}", extra=query_params)

	query_result = table.query(**query_params)
	query_items = query_result['Items']
	record_count = query_result['Count']

	# A LastEvaluatedKey will be present if a limited Query was performed and if the amount of matching objects exceeds
	# the limit value. Only get records up to the limit if provided
	if limit:
		# Continue to query if the LastEvaluatedKey (more pages) attribute is present and add to the items list up to the limit
		while query_result.get('LastEvaluatedKey', False) and record_count < limit:
			# The max items returned per operation is 1000
			# If there are less than 1000 records remaining before hitting the limit, use the remaining value
			if limit - record_count < 1000:
				query_params['Limit'] = limit - record_count

			query_params['ExclusiveStartKey'] = query_result.get('LastEvaluatedKey')
			query_result = table.query(**query_params)
			query_items.extend(query_result['Items'])
			record_count += query_result['Count']
	else:
		# Continue to query if the LastEvaluatedKey (more pages) attribute is present and add to the items list up to the limit
		while query_result.get('LastEvaluatedKey', False):
			query_params['ExclusiveStartKey'] = query_result.get('LastEvaluatedKey')
			query_result = table.query(**query_params)
			query_items.extend(query_result['Items'])
			record_count += query_result['Count']

	logger.info(f"Retrieved {record_count} records from query", extra=query_params)

	return query_items
