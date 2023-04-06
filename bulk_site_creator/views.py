import json
import logging
from typing import Optional

import boto3
from canvas_api.helpers import accounts as canvas_api_accounts
from canvas_course_site_wizard.models import CanvasSchoolTemplate
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_utils import \
    SessionInactivityExpirationRC  # TODO replace this
from icommons_common.models import (  # TODO: update to coursemanager.models
    CourseGroup, Department)
from lti_permissions.decorators import lti_permission_required

from common.utils import (get_canvas_site_template,
                          get_canvas_site_templates_for_school, get_term_data,
                          get_term_data_for_school)

from .schema import JobRecord
from .utils import (batch_write_item, generate_task_objects,
                    get_course_instance_query_set,
                    get_course_instances_without_canvas_sites)

logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def index(request):
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    term_ids, _current_term_id_id = get_term_data_for_school(sis_account_id)
    school_id = sis_account_id.split(":")[1]
    canvas_site_templates = get_canvas_site_templates_for_school(school_id)
    potential_course_sites_query = None

    if request.method == "POST":
        selected_term_id = request.POST["course-term_id"]
        # Retrieve all course instances for the given term_id and account that do not have Canvas course sites
        # nor are set to be fed into Canvas via the automated feed
        potential_course_sites_query = get_course_instance_query_set(
            selected_term_id, sis_account_id
        ).filter(canvas_course_id__isnull=True, sync_to_canvas=0)

    # TODO maybe better to use template tag unless used elsewhere?
    potential_course_site_count = (
        potential_course_sites_query.count() if potential_course_sites_query else 0
    )

    context = {
        "term_ids": term_ids,
        "potential_course_sites": potential_course_sites_query,
        "potential_site_count": potential_course_site_count,
        "canvas_site_templates": canvas_site_templates,
    }
    return render(request, "bulk_site_creator/index.html", context=context)


@login_required
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["POST"])
def create_bulk_job(request: HttpRequest) -> Optional[JsonResponse]:
    user_id = request.LTI["lis_person_sourcedid"]
    user_full_name = request.LTI["list_person_name_full"]
    user_email = request.LTI["lis_person_contact_email_primary"]

    data = json.loads(request.POST["data"])
    filters = data["filters"]

    term_id = filters.get("term_id")
    term_name = get_term_data(term_id).get("name")

    school_account_id = filters["school"]
    (_, school_id) = canvas_api_accounts.parse_canvas_account_id(school_account_id)

    department_id = None
    department_account_id = filters.get("department")
    if department_account_id:
        (_, department_id) = department_account_id.split(":")

    try:
        department_name = Department.objects.get(department_id=department_id).name
    except Department.DoesNotExist as e:
        logger.error(f"Department {department_id} does not exist: {e}")
        return JsonResponse({"error": "Department does not exist"}, status=400)

    course_group_id = None
    course_group_account_id = filters.get("course_group")
    if course_group_account_id:
        (_, course_group_id) = course_group_account_id.split(":")

    try:
        course_group_name = CourseGroup.objects.get(course_group_id=course_group_id).name
    except CourseGroup.DoesNotExist as e:
        logger.error(f"Course Group {course_group_id} does not exist: {e}")
        return JsonResponse({"error": "Course Group does not exist"}, status=400)

    template_id = data.get("template")
    try:
        template_name = get_canvas_site_template(school_id, template_id).name
    except CanvasSchoolTemplate.DoesNotExist as e:
        logger.error(f"Template {template_id} does not exist: {e}")
        return JsonResponse({"error": "Template does not exist"}, status=400)

    # If the create_all flag has been set and passed with the form,
    # then create a query to get the all course instances with the applied filters that are to be created.
    if data.get("create_all", False):
        # Get the account data to be used in the course instance query.
        if filters["course_group"]:
            account = course_group_id
        elif filters["department"]:
            account = department_id
        else:
            account = school_account_id

        course_instance_ids = get_course_instances_without_canvas_sites(account, term_id)
    else:
        course_instance_ids = data["course_instance_ids"]

    # Create JobRecord object first so we can reference the job_id in the TaskRecord objects
    try:
        job = JobRecord(
            user_id=user_id,
            user_full_name=user_full_name,
            user_email=user_email,
            school=school_id,
            term_id=term_id,
            term_name=term_name,
            department_id=department_id,
            department_name=department_name,
            course_group_id=course_group_id,
            course_group_name=course_group_name,
            template_id=template_id,
            template_name=template_name,
            workflow_state="PENDING",
        )
    except (TypeError, ValueError) as e:
        logger.error(f"Unexpected input during JobRecord creation: {e}")
        return JsonResponse({"status": 400})

    # Create TaskRecord objects for each course instance
    try:
        tasks = generate_task_objects(course_instance_ids, job)
    except (TypeError, ValueError) as e:
        return JsonResponse({"status": 400})

    dynamodb = boto3.resource("dynamodb")
    table_name = settings.BULK_COURSE_CREATION.get("dynamo_table_name")
    table = dynamodb.Table(table_name)

    # Write the TaskRecords to DynamoDB. We insert these first since the subsequent JobRecord
    # kicks off the downstream bulk workflow via a DynamoDB stream.
    batch_write_item(table, tasks)

    # Now write the JobRecord to DynamoDB
    response = table.put_item(job.to_dict())
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        logger.error(f"Error adding JobRecord to DynamoDB: {response}")
        return JsonResponse({"status": 500})
    return JsonResponse({"status": 200})
