import json
import logging
from typing import Optional

import boto3
from canvas_api.helpers import accounts as canvas_api_accounts
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_utils import (
    SessionInactivityExpirationRC,
)  # TODO replace this
from icommons_common.models import CourseInstance, School
from lti_permissions.decorators import lti_permission_required

from common.utils import get_canvas_site_templates_for_school, get_term_data_for_school

from .schema import JobRecord, TaskRecord
from .utils import batch_write_item

logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def index(request):
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    terms, _current_term_id = get_term_data_for_school(sis_account_id)
    school_id = sis_account_id.split(":")[1]
    school = School.objects.get(school_id=school_id)
    canvas_site_templates = get_canvas_site_templates_for_school(school_id)
    potential_course_sites_query = None

    if request.method == "POST":
        selected_term = request.POST["course-term"]
        selected_template = request.POST["template-select"]
        # Retrieve all course instances for the given term and account that do not have Canvas course sites
        # nor are set to be fed into Canvas via the automated feed
        potential_course_sites_query = get_course_instance_query_set(
            selected_term, sis_account_id
        ).filter(canvas_course_id__isnull=True, sync_to_canvas=0)

    # TODO maybe better to use template tag unless used elsewhere?
    potential_course_site_count = (
        potential_course_sites_query.count() if potential_course_sites_query else 0
    )

    context = {
        "terms": terms,
        "potential_course_sites": potential_course_sites_query,
        "potential_site_count": potential_course_site_count,
        "canvas_site_templates": canvas_site_templates,
    }
    return render(request, "bulk_site_creator/index.html", context=context)


@login_required
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["POST"])
def create_bulk_job(request: HttpRequest) -> Optional[JsonResponse]:
    canvas_user_id = request.LTI["custom_canvas_user_id"]
    logged_in_user_id = request.LTI["lis_person_sourcedid"]
    user_email = request.LTI["lis_person_contact_email_primary"]
    user_full_name = request.LTI["list_person_name_full"]

    data = json.loads(request.POST["data"])
    template_id = data.get("template")
    template_name = data.get("template_name")
    term_id = data.get("term_id")
    term_name = data.get("term_name")
    filters = data["filters"]
    term = filters.get("term")

    school_account_id = filters["school"]
    (_, school_id) = canvas_api_accounts.parse_canvas_account_id(school_account_id)

    department = None
    department_account_id = filters.get("department")
    if department_account_id:
        (_, department) = department_account_id.split(":")

    course_group = None
    course_group_account_id = filters.get("course_group")
    if course_group_account_id:
        (_, course_group) = course_group_account_id.split(":")

    created_by_user_id = logged_in_user_id
    if not created_by_user_id:
        created_by_user_id = f"canvas_user_id:{canvas_user_id}"

    # If the create_all flag has been set and passed with the form,
    # then create a query to get the all course instances with the applied filters that are to be created.
    course_instance_ids = []
    if data.get("create_all", False):
        # Get the account data to be used in the course instance query.
        if filters["course_group"]:
            account = course_group
        elif filters["department"]:
            account = department
        else:
            account = school_account_id

        # Retrieve all course instances for the given term and account that do not have Canvas course sites
        # nor are set to be fed into Canvas via the automated feed
        ci_query_set_without_canvas = get_course_instance_query_set(
            term, account
        ).filter(canvas_course_id__isnull=True, sync_to_canvas=0)

        # Iterate through the query set to build a list of all the course instance id's
        # for a school/course_group/department, which course sites will be created for.
        for ci in ci_query_set_without_canvas:
            course_instance_ids.append(ci.course_instance_id)
    else:
        course_instance_ids = data["course_instance_ids"]

    # Create JobRecord object first so we can reference the job_id in the TaskRecord objects
    try:
        job = JobRecord(
            school_id,
            term,
            department,
            course_group,
            created_by_user_id,
            course_instance_ids,
            "pending",
            user_email,
            user_full_name,
            template_name,
            template_id,
        )
    except (TypeError, ValueError) as e:
        logger.error(f"Unexpected input during JobRecord creation: {e}")
        return JsonResponse({"status": 500})

    tasks = []
    for ci_id in course_instance_ids:
        try:
            task = TaskRecord(job, ci_id, created_by_user_id, "pending").to_dict()
            tasks.append(task)
        except (TypeError, ValueError) as e:
            logger.error(f"Error creating TaskRecord for job {job['job_id']}: {e}")
            return JsonResponse({"status": 500})

    dynamodb = boto3.resource("dynamodb")
    # TODO: Make SSM parameter
    table_name = "bulk-enrollment-tool-backend-dev-DynamoDbTable-305A936QYVK9"
    table = dynamodb.Table(table_name)

    # Write the TaskRecords to DynamoDB
    batch_write_item(table, tasks)

    # Now write the JobRecord to DynamoDB
    response = table.put_item(job.to_dict())
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        logger.error(f"Error adding JobRecord to DynamoDB: {response}")
        return JsonResponse({"status": 500})
    return JsonResponse({"status": 200})


#  TODO Currently a method in canvas_site_creator models, using for temp testing
def get_course_instance_query_set(sis_term_id, sis_account_id):
    # Exclude records that have parent_course_instance_id  set(TLT-3558) as we don't want to create sites for the
    # children; they will be associated with the parent site
    filters = {
        "exclude_from_isites": 0,
        "term_id": sis_term_id,
        "parent_course_instance_id__isnull": True,
    }

    logger.debug(
        f"Getting CI objects for term: {sis_term_id} and school: {sis_account_id}"
    )

    (account_type, account_id) = sis_account_id.split(":")
    if account_type == "school":
        filters["course__school"] = account_id
    elif account_type == "dept":
        filters["course__department"] = account_id
    elif account_type == "coursegroup":
        filters["course__course_group"] = account_id

    return CourseInstance.objects.filter(**filters)
