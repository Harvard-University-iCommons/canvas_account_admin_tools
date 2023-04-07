import logging

from botocore.exceptions import ClientError
from icommons_common.models import (  # TODO: update to coursemanager.models
    CourseInstance, Department)

from common.utils import get_canvas_site_template, get_term_data

from .schema import JobRecord, TaskRecord

logger = logging.getLogger(__name__)

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html#batch-writing
def batch_write_item(table, items: list[dict]):
    try:
        with table.batch_writer() as batch:
            for item in items:
                response = batch.put_item(Item=item)
                logging.info(response)
    except ClientError as e:
        logging.error(e.response["Error"]["Message"])

def generate_task_objects(course_instance_ids: list[str], job: JobRecord):
    tasks = []
    for ci_id in course_instance_ids:
        try:
            task = TaskRecord(job_record=job, course_instance_id=ci_id, workflow_state='PENDING').to_dict()
            tasks.append(task)
        except (TypeError, ValueError) as e:
            logging.error(f"Error creating TaskRecord for job {job['job_id']}: {e}")
            raise
    return tasks

def get_course_instances_without_canvas_sites(account, term_id):
    # Retrieve all course instances for the given term_id and account that do not have Canvas course sites
    # nor are set to be fed into Canvas via the automated feed
    ci_query_set_without_canvas = get_course_instance_query_set(
        term_id, account
    ).filter(canvas_course_id__isnull=True, sync_to_canvas=0)

    # Iterate through the query set to build a list of all the course instance id's
    # for a school/course_group/department, which course sites will be created for.
    course_instance_ids = []
    for ci in ci_query_set_without_canvas:
        course_instance_ids.append(ci.course_instance_id)

    return course_instance_ids

#  TODO Currently a method in canvas_site_creator models, using for temp testing
def get_course_instance_query_set(sis_term_id_id, sis_account_id):
    # Exclude records that have parent_course_instance_id  set(TLT-3558) as we don't want to create sites for the
    # children; they will be associated with the parent site
    filters = {
        "exclude_from_isites": 0,
        "term_id_id": sis_term_id_id,
        "parent_course_instance_id__isnull": True,
    }

    logger.debug(
        f"Getting CI objects for term_id: {sis_term_id_id} and school: {sis_account_id}"
    )

    (account_type, account_id) = sis_account_id.split(":")
    if account_type == "school":
        filters["course__school"] = account_id
    elif account_type == "dept":
        filters["course__department"] = account_id
    elif account_type == "coursegroup":
        filters["course__course_group"] = account_id

    return CourseInstance.objects.filter(**filters)

def get_term_name_by_id(term_id: str):
    return get_term_data(term_id).get("name")

def get_department_name_by_id(department_id: str):
    return Department.objects.get(department_id=department_id).name
