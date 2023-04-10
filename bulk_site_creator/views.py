import json
import logging
from typing import Optional

import boto3

from botocore.exceptions import ClientError

from canvas_course_site_wizard.models import CanvasSchoolTemplate
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts
from icommons_common.canvas_utils import \
    SessionInactivityExpirationRC  # TODO replace this
from icommons_common.models import (  # TODO: update to coursemanager.models
    CourseGroup, Department, Term)
from lti_permissions.decorators import lti_permission_required

from common.utils import (get_canvas_site_template,
                          get_school_data_for_sis_account_id,
                          get_canvas_site_templates_for_school,
                          get_term_data_for_school,
                          get_department_data_for_school,
                          get_course_group_data_for_school)
from .schema import JobRecord
from .utils import (batch_write_item,
                    generate_task_objects,
                    get_course_instance_query_set,
                    get_course_instances_without_canvas_sites,
                    get_department_name_by_id, get_term_name_by_id)
from boto3.dynamodb.conditions import Key
from ulid import ULID

logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

dynamodb = boto3.resource("dynamodb")
table_name = settings.BULK_COURSE_CREATION.get("site_creator_dynamo_table_name")
table = dynamodb.Table(table_name)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def index(request):
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_key = f'SCHOOL#{school_id.upper()}'
    query_params = {
        'KeyConditionExpression': Key('pk').eq(school_key),
        'ScanIndexForward': False,
    }
    jobs_for_school = table.query(**query_params)['Items']

    context = {
        'jobs_for_school': jobs_for_school
    }
    return render(request, "bulk_site_creator/index.html", context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def job_detail(request, job_id):
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_key = f'SCHOOL#{school_id.upper()}'
    job_query_params = {
        'KeyConditionExpression': Key('pk').eq(school_key) & Key('sk').eq(job_id),
        'ScanIndexForward': False,
    }
    job = table.query(**job_query_params)['Items'][0]

    tasks_query_params = {
        'KeyConditionExpression': Key('pk').eq(job_id),
        'ScanIndexForward': False,
    }
    tasks = table.query(**tasks_query_params)['Items']

    context = {
        'job': job,
        'tasks': tasks
    }
    return render(request, "bulk_site_creator/job_detail.html", context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def new_job(request):
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    terms, _current_term_id = get_term_data_for_school(sis_account_id)
    school_id = sis_account_id.split(":")[1]
    canvas_site_templates = get_canvas_site_templates_for_school(school_id)
    potential_course_sites_query = None
    departments = []
    course_groups = []

    try:
        departments = get_department_data_for_school(sis_account_id)
    except Exception:
        message = f"Failed to get departments with sis_account_id {sis_account_id}"
        logger.exception(message)

    try:
        course_groups = get_course_group_data_for_school(sis_account_id)
    except Exception:
        message = f"Failed to get course groups with sis_account_id {sis_account_id}"
        logger.exception(message)

    if request.method == "POST":
        selected_term_id = request.POST["course-term"]
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
        "terms": terms,
        "potential_course_sites": potential_course_sites_query,
        "potential_site_count": potential_course_site_count,
        "canvas_site_templates": canvas_site_templates,
        "departments": departments,
        "course_groups": course_groups
    }

    return render(request, "bulk_site_creator/new_job.html", context=context)


@login_required
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["POST"])
def create_bulk_job(request: HttpRequest) -> Optional[JsonResponse]:
    user_id = request.LTI["lis_person_sourcedid"]
    user_full_name = request.LTI["lis_person_name_full"]
    user_email = request.LTI["lis_person_contact_email_primary"]

    data = json.loads(request.body)
    filters = data["filters"]

    term_id = filters.get("term")
    if term_id:
        try:
            term_name = get_term_name_by_id(term_id)
        except Term.DoesNotExist as e:
            logger.info(f"Term {term_id} does not exist: {e}")
            return JsonResponse({"error": "Term does not exist"}, status=400)
    else:
        term_name = None

    school_account_id = filters["school"]
    (_, school_id) = canvas_api_accounts.parse_canvas_account_id(school_account_id)

    department_id = None
    department_account_id = filters.get("department")
    if department_account_id:
        (_, department_id) = department_account_id.split(":")

    if department_id:
        try:
            department_name = get_department_name_by_id(department_id)
        except Department.DoesNotExist as e:
            logger.info(f"Department {department_id} does not exist: {e}")
            return JsonResponse({"error": "Department does not exist"}, status=400)
    else:
        department_name = None

    course_group_id = None
    course_group_account_id = filters.get("course_group")
    if course_group_account_id:
        (_, course_group_id) = course_group_account_id.split(":")

    if course_group_id:
        try:
            course_group_name = CourseGroup.objects.get(course_group_id=course_group_id).name
        except CourseGroup.DoesNotExist as e:
            logger.info(f"Course Group {course_group_id} does not exist: {e}")
            return JsonResponse({"error": "Course Group does not exist"}, status=400)
    else:
        course_group_name = None

    template_id = data.get("template")

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

    # Write the TaskRecords to DynamoDB. We insert these first since the subsequent JobRecord
    # kicks off the downstream bulk workflow via a DynamoDB stream.
    try:
        batch_write_item(table, tasks)
    except ClientError as e:
        return JsonResponse({"status": 500})

    # Now write the JobRecord to DynamoDB
    response = table.put_item(Item=job.to_dict())
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        logger.error(f"Error adding JobRecord to DynamoDB: {response}")
        return JsonResponse({"status": 500})
    return JsonResponse({"status": 200})
