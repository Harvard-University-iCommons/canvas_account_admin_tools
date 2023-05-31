import json
import logging
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key
from canvas_sdk import RequestContext
from coursemanager.models import CourseGroup, Term, Department
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required

from common.utils import (get_canvas_site_templates_for_school,
                          get_course_group_data_for_school,
                          get_department_data_for_school,
                          get_term_data_for_school,
                          get_canvas_site_template_name)

from .schema import JobRecord
from .utils import batch_write_item, generate_task_objects, get_course_instance_query_set


logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)

dynamodb = boto3.resource("dynamodb")
table_name = settings.BULK_COURSE_CREATION.get("site_creator_dynamo_table_name")

# TODO improve logging for CRUD actions
# TODO add documentation to each view


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def index(request):
    table = dynamodb.Table(table_name)
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_key = f'SCHOOL#{school_id.upper()}'
    query_params = {
        'KeyConditionExpression': Key('pk').eq(school_key),
        'ScanIndexForward': False,
    }
    jobs_for_school = table.query(**query_params)['Items']

    # Update string timestamp to datetime.
    [item.update(created_at=parse_datetime(item['created_at']))
     for item in jobs_for_school]

    context = {
        'jobs_for_school': jobs_for_school
    }
    return render(request, "bulk_site_creator/index.html", context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET"])
def job_detail(request, job_id):
    table = dynamodb.Table(table_name)
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_key = f'SCHOOL#{school_id.upper()}'
    job_query_params = {
        'KeyConditionExpression': Key('pk').eq(school_key) & Key('sk').eq(job_id),
        'ScanIndexForward': False,
    }
    job = table.query(**job_query_params)['Items'][0]

    # Update string timestamp to datetime.
    job.update(created_at=parse_datetime(job['created_at']))
    job.update(updated_at=parse_datetime(job['updated_at']))

    tasks_query_params = {
        'KeyConditionExpression': Key('pk').eq(job_id),
        'ScanIndexForward': False,
    }
    tasks = table.query(**tasks_query_params)['Items']

    context = {
        'job': job,
        'tasks': tasks,
        'canvas_url': settings.CANVAS_URL,
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
    selected_term_id = None
    selected_course_group_id = None
    selected_department_id = None

    # Only display the Course Groups dropdown if the tool is launched in the COLGSAS sub-account
    if school_id == 'colgsas':
        try:
            course_groups = get_course_group_data_for_school(sis_account_id)
        except Exception:
            logger.exception(f"Failed to get course groups with sis_account_id {sis_account_id}")
    # For all other schools, display just the Departments dropdown
    else:
        try:
            departments = get_department_data_for_school(sis_account_id)
        except Exception:
            logger.exception(f"Failed to get departments with sis_account_id {sis_account_id}")

    if request.method == "POST":
        selected_term_id = request.POST.get("courseTerm", None)
        selected_course_group_id = request.POST.get("courseCourseGroup", None)
        selected_department_id = request.POST.get("courseDepartment", None)

        # Retrieve all course instances for the given term_id and account that do not have Canvas course sites
        # nor are set to be fed into Canvas via the automated feed
        potential_course_sites_query = get_course_instance_query_set(
            selected_term_id, sis_account_id
        ).filter(canvas_course_id__isnull=True,
                 sync_to_canvas=0,
                 bulk_processing=0,
                 term__term_id=selected_term_id)

        # Filter potential_course_sites_query by course group.
        if selected_course_group_id and selected_course_group_id != '0':
            potential_course_sites_query = potential_course_sites_query.filter(course__course_group=selected_course_group_id)
        # Filter potential_course_sites_query by department.
        elif selected_department_id and selected_department_id != '0':
            potential_course_sites_query = potential_course_sites_query.filter(course__department=selected_department_id)

    # TODO maybe better to use template tag unless used elsewhere?
    # TODO cont. this may be included in a summary generation to be displayed in page (see wireframe and Jira ticket)
    potential_course_site_count = (
        potential_course_sites_query.count() if potential_course_sites_query else 0
    )

    context = {
        "terms": terms,
        "potential_course_sites": potential_course_sites_query,
        "potential_site_count": potential_course_site_count,
        "canvas_site_templates": canvas_site_templates,
        "departments": departments,
        "course_groups": course_groups,
        'selected_term_id': selected_term_id,
        'selected_course_group_id': selected_course_group_id,
        'selected_department_id': selected_department_id
    }
    return render(request, "bulk_site_creator/new_job.html", context=context)


@login_required
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["POST"])
def create_bulk_job(request: HttpRequest) -> Optional[JsonResponse]:
    dynamodb_table = dynamodb.Table(table_name)
    user_id = request.LTI["lis_person_sourcedid"]
    user_full_name = request.LTI["lis_person_name_full"]
    user_email = request.LTI["lis_person_contact_email_primary"]
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]

    table_data = json.loads(request.POST['data'])

    term_id = request.POST['termID']
    term = Term.objects.get(term_id=term_id)
    term_name = term.display_name
    sis_term_id = term.meta_term_id()
    course_group_id = request.POST['courseGroupID']
    course_group_name = None
    department_id = request.POST['departmentID']
    department_name = None
    create_all = table_data['create_all']
    course_instance_ids = table_data['course_instance_ids']
    template_id = table_data['template']
    template_name = get_canvas_site_template_name(template_id)

    if create_all:
        # Get all course instance records that will have Canvas sites created by filtering on the
        # term and (course group or department) values
        # Also filter on the 'bulk_processing' flag to avoid multiple job submission conflicts
        potential_course_sites_query = get_course_instance_query_set(
            term_id, sis_account_id
        ).filter(canvas_course_id__isnull=True,
                 sync_to_canvas=0,
                 bulk_processing=0).select_related('course')

        # Check if a course group or department filter needs to be applied to queryset
        # The value of 0 is for the default option of no selected Department/Course Group
        if school_id == 'colgsas':
            if course_group_id and course_group_id != '0':
                course_group_name = CourseGroup.objects.get(course_group_id=course_group_id).name
                potential_course_sites_query = potential_course_sites_query.filter(course__course_group=course_group_id)
        else:
            if department_id and department_id != '0':
                department_name = Department.objects.get(department_id=department_id).name
                potential_course_sites_query = potential_course_sites_query.filter(course__department=department_id)

    else:
        # Get all potential course instances for the selected term in the account
        # Further filter by the selected course instances from the DataTable
        potential_course_sites_query = get_course_instance_query_set(
            term_id, sis_account_id
        ).filter(canvas_course_id__isnull=True,
                 sync_to_canvas=0,
                 bulk_processing=0,
                 course_instance_id__in=course_instance_ids).select_related('course')

    if potential_course_sites_query.count() > 0:
        job = JobRecord(
            sis_account_id=sis_account_id,
            user_id=user_id,
            user_full_name=user_full_name,
            user_email=user_email,
            school=school_id,
            term_id=term_id,
            sis_term_id=sis_term_id,
            term_name=term_name,
            department_id=department_id,
            department_name=department_name,
            course_group_id=course_group_id,
            course_group_name=course_group_name,
            template_id=template_id,
            template_name=template_name,
            workflow_state="pending",
        )

        # Create TaskRecord objects for each course instance
        tasks = generate_task_objects(potential_course_sites_query, job)

        # Set the bulk_processing field to true for all course instances being processed by this job so they
        # do not show up in the new job page
        potential_course_sites_query.update(bulk_processing=True)

        # Write the TaskRecords to DynamoDB. We insert these first since the subsequent JobRecord
        # kicks off the downstream bulk workflow via a DynamoDB stream.
        batch_write_item(dynamodb_table, tasks)

        # Now write the JobRecord to DynamoDB
        response = dynamodb_table.put_item(Item=job.to_dict())
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            logger.error(f"Error adding JobRecord to DynamoDB: {response}")
            # TODO improve this logging statement

        messages.add_message(request, messages.SUCCESS, 'Bulk job created')
    else:
        messages.add_message(request, messages.WARNING, 'No potential course sites available with provided filters')

    return redirect('bulk_site_creator:index')
