import json
import logging
from typing import Optional

import boto3
from django.contrib import messages
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from canvas_api.helpers import accounts as canvas_api_accounts
from canvas_account_admin_tools.models import CanvasSchoolTemplate
from canvas_sdk import RequestContext
from coursemanager.models import CourseGroup, Department, Term
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required


from common.utils import (get_canvas_site_template,
                          get_canvas_site_templates_for_school,
                          get_course_group_data_for_school,
                          get_department_data_for_school,
                          get_school_data_for_sis_account_id,
                          get_term_data_for_school)

from .schema import JobRecord
from .utils import (batch_write_item, generate_task_objects,
                    get_course_instance_query_set,
                    get_course_instances_without_canvas_sites,
                    get_department_name_by_id, get_term_name_by_id)


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
    selected_term_id = None
    selected_course_group_id = None
    selected_department_id = None

    # Only display the Course Groups dropdown if the tool is launched in the COLGSAS sub-account
    print('request ------------------------------>', request.POST)
    print('school_id ------------------------------>', school_id)
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
        # TODO Add bulk_processing flag to filter
        # if school_id == 'colgsas':
        #     if selected_course_group_id == '0':
        #         print('selected_term_id ------------------------------>', selected_term_id)
        #     else:
        #         print('selected_term_id, selected_department_id------------------------------>', selected_term_id, selected_course_group_id.split(":")[1])
        # else:
        #     print('selected_term_id, selected_department_id------------------------------>', selected_term_id, selected_department_id)
        if selected_course_group_id or selected_department_id:
            if selected_course_group_id == '0' or selected_department_id == '0':
                potential_course_sites_query = get_course_instance_query_set(
                    selected_term_id, sis_account_id
                ).filter(canvas_course_id__isnull=True,
                         sync_to_canvas=0,
                         term__term_id=selected_term_id)
            elif selected_course_group_id:
                potential_course_sites_query = get_course_instance_query_set(
                    selected_term_id, sis_account_id
                ).filter(canvas_course_id__isnull=True,
                         sync_to_canvas=0,
                         term__term_id=selected_term_id,
                         course__course_group=selected_course_group_id.split(":")[1])
            elif selected_department_id:
                potential_course_sites_query = get_course_instance_query_set(
                    selected_term_id, sis_account_id
                ).filter(canvas_course_id__isnull=True,
                         sync_to_canvas=0,
                         term__term_id=selected_term_id,
                         course__departments=selected_department_id.split(":")[1])

            # potential_course_sites_query = get_course_instance_query_set(
            #     selected_term_id, sis_account_id
            # ).filter(canvas_course_id__isnull=True, sync_to_canvas=0)

            print('potential_course_sites_query ------------------------------>', potential_course_sites_query)
            print('selected_department_id ------------------------------>', selected_department_id)
            print('selected_course_group_id ------------------------------>', selected_course_group_id)


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
    # TODO - Set 'bulk_processing' flag to true for all course instances processed by this view before inserting into DynamoDB
    dynamodb_table = dynamodb.Table(table_name)
    user_id = request.LTI["lis_person_sourcedid"]
    user_full_name = request.LTI["lis_person_name_full"]
    user_email = request.LTI["lis_person_contact_email_primary"]
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_name = request.LTI["context_title"] # TODO add this to Job record

    table_data = json.loads(request.POST['data'])

    term_id = request.POST['termID']
    term_name = get_term_name_by_id(term_id)
    course_group_id = request.POST['courseGroupID']
    course_group_name = None
    department_id = request.POST['departmentID']
    department_name = None
    create_all = table_data['create_all']
    course_instance_ids = table_data['course_instance_ids']
    template_id = table_data['template']

    if create_all:
        # Get all course instance records that will have Canvas sites created by filtering on the
        # term and (course group or department) values
        # Also filter on the 'bulk_processing' flag to avoid multiple job submission conflicts
        # TODO Add bulk_processing flag to filter
        potential_course_sites_query = get_course_instance_query_set(
            term_id, sis_account_id
        ).filter(canvas_course_id__isnull=True, sync_to_canvas=0)

        # Check if a course group or department filter needs to be applied to queryset
        # The value of 0 is for the default option of no selected Department/Course Group
        if school_id == 'colgsas':
            if course_group_id and course_group_id != '0':
                course_group_name = CourseGroup.objects.get(course_group_id=course_group_id).name
                potential_course_sites_query = potential_course_sites_query.filter(course__course_group=course_group_id.split(":")[1])
        else:
            if department_id and department_id != '0':
                department_name = get_department_name_by_id(department_id)
                potential_course_sites_query = potential_course_sites_query.filter(course__department=department_id.split(":")[1])

        if potential_course_sites_query.count() > 0:
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
                workflow_state="pending",
            )

            # Create TaskRecord objects for each course instance
            tasks = generate_task_objects(potential_course_sites_query, job)

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

    else:
        # TODO Abstraction - This block can potentially be pulled outside of the first condition check or separate method
        # TODO cont. - Think about error handling and reeverting that fflag on exception
        # Create tasks for each of the selected course instance IDs
        if course_instance_ids:
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
                workflow_state="pending",
            )

            course_instances = CourseInstance.objects.filter(course_instance_id__in=course_instance_ids)

            # Create TaskRecord objects for each course instance
            tasks = generate_task_objects(course_instances, job)

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
