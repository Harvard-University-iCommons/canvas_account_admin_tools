import logging

from botocore.exceptions import ClientError
from coursemanager.models import CourseInstance, Department

from common.utils import get_canvas_site_template, get_term_data

from .schema import JobRecord, TaskRecord

logger = logging.getLogger(__name__)

# TODO add documentation to each method

# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html#batch-writing
def batch_write_item(table, items: list[dict]):
    try:
        with table.batch_writer() as batch:
            for item in items:
                response = batch.put_item(Item=item)
                logging.info(response)
    except ClientError as e:
        logging.error(f"Error writing to DynamoDB: {e}")
        raise


def generate_task_objects(course_instances: list[dict], job: JobRecord):
    tasks = []
    for ci in course_instances:
        try:
            # course_code block taken from feed_course_sections_enrollments
            # management command in the canvas_integration project
            course_code = None
            if ci.short_title != '':
                course_code = ci.short_title
            elif ci.course.registrar_code_display != '':
                course_code = ci.course.registrar_code_display
            else:
                course_code = ci.course.registrar_code

            if ci.course.course_group:
                sis_account_id = f"sis_account_id:coursegroup:{ci.course.course_group_id}"
            elif ci.course.department:
                sis_account_id = f"sis_account_id:department:{ci.course.department_id}"
            else:
                sis_account_id = f"sis_account_id:school:{ci.course.school_id}"

            task = TaskRecord(job_record=job,
                              course_instance_id=ci.course_instance_id,
                              course_code=course_code,
                              course_title=ci.title,
                              short_title=ci.short_title,
                              canvas_course_id=ci.canvas_course_id,
                              department_id=ci.course.department_id,
                              course_group_id=ci.course.course_group_id,
                              sis_account_id=sis_account_id,
                              section=ci.section,
                              workflow_state='pending').to_dict()
            tasks.append(task)
        except (TypeError, ValueError) as e:
            logging.error(f"Error creating TaskRecord for job {job.sk}: {e}")
            raise
    return tasks


def get_course_instance_query_set(sis_term_id, sis_account_id):
    # Exclude records that have parent_course_instance_id  set(TLT-3558) as we don't want to create sites for the
    # children; they will be associated with the parent site
    filters = {
        "exclude_from_isites": 0,
        "term_id": sis_term_id,
        "parent_course_instance_id__isnull": True,
    }

    logger.debug(
        f"Getting CI objects for term_id: {sis_term_id} and school: {sis_account_id}"
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
