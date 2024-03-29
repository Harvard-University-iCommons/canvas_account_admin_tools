import json
import logging
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key
from canvas_sdk import RequestContext
from coursemanager.models import CourseGroup, Department, Term
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required

from common.utils import (get_canvas_site_template_name,
                          get_canvas_site_templates_for_school,
                          get_course_group_data_for_school,
                          get_department_data_for_school,
                          get_term_data_for_school)

from .schema import JobRecord
from .utils import (batch_write_item, generate_task_objects,
                    get_course_instance_query_set)

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
    """
    This function renders the Bulk Site Creator index page
    consisting of bulk creation jobs (if any).
    """
    table = dynamodb.Table(table_name)
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_key = f'SCHOOL#{school_id.upper()}'
    query_params = {
        'KeyConditionExpression': Key('pk').eq(school_key),
        'ScanIndexForward': False,
    }
    logger.debug(f'Retrieving jobs for school {school_key}.')
    jobs_for_school = table.query(**query_params)['Items']

    # Update created_at (ISO8601) string timestamp to datetime.
    [item.update(created_at=parse_datetime(item['created_at']))
     for item in jobs_for_school]

    context = {
        'jobs_for_school': jobs_for_school
    }
    logger.debug(f'Retrieved jobs for school {school_key}.', extra=context)
    return render(request, "bulk_site_creator/index.html", context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET"])
def job_detail(request: HttpRequest, job_id: str) -> HttpResponse:
    """
    This function renders the Bulk Site Creator job detail page
    with details about a job and the tasks for that job.
    """
    table = dynamodb.Table(table_name)
    sis_account_id = request.LTI["custom_canvas_account_sis_id"]
    school_id = sis_account_id.split(":")[1]
    school_key = f'SCHOOL#{school_id.upper()}'
    job_query_params = {
        'KeyConditionExpression': Key('pk').eq(school_key) & Key('sk').eq(job_id),
        'ScanIndexForward': False,
    }
    logger.debug(f'Retrieving job details for job {job_id}.')
    job = table.query(**job_query_params)['Items'][0]

    # Update string timestamp to datetime.
    job.update(created_at=parse_datetime(job['created_at']))
    job.update(updated_at=parse_datetime(job['updated_at']))

    tasks_query_params = {
        'KeyConditionExpression': Key('pk').eq(job_id),
        'ScanIndexForward': False,
    }
    task_query_result = table.query(**tasks_query_params)
    tasks = task_query_result['Items']

    # If there are additional items to be retrieved for this job, the LastEvaluatedKey will be present
    # Use this key as the starting point for subsequent queries to build a full list
    while task_query_result.get('LastEvaluatedKey', False):
        tasks_query_params['ExclusiveStartKey'] = task_query_result.get('LastEvaluatedKey')
        task_query_result = table.query(**tasks_query_params)
        tasks.extend(task_query_result['Items'])

    context = {
        'job': job,
        'tasks': tasks,
        'canvas_url': settings.CANVAS_URL
    }
    logger.debug(f'Retrieved job details for job {job_id}.', extra=context)
    return render(request, "bulk_site_creator/job_detail.html", context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["GET", "POST"])
def new_job(request):
    """
    This function renders the Bulk Site Creator new job page with
    potential course sites for Canvas course site creation.
    """
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
            course_groups = get_course_group_data_for_school(sis_account_id, include_ile_sb=False)
        except Exception:
            logger.exception(f"Failed to get course groups with sis_account_id {sis_account_id}")
    # For all other schools, display just the Departments dropdown
    else:
        try:
            departments = get_department_data_for_school(sis_account_id, include_ile_sb=False)
        except Exception:
            logger.exception(f"Failed to get departments with sis_account_id {sis_account_id}")

    logging_dept_cg_text = ' and no selected department or course group'
    if request.method == "POST":
        selected_term_id = request.POST.get("courseTerm", None)
        selected_course_group_id = request.POST.get("courseCourseGroup", None)
        selected_department_id = request.POST.get("courseDepartment", None)

        logging_dept_cg_text = f' and course group ID {selected_course_group_id}' if selected_course_group_id \
            else f' and department ID {selected_department_id}' if selected_department_id \
            else ' and no selected department or course group.'
        logger.debug(f'Retrieving potential course sites for term ID '
                     f'{selected_term_id}{logging_dept_cg_text}', extra={"sis_account_id": sis_account_id,
                                                                         "school_id": school_id,
                                                                         })

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
            selected_course_group_id = int(selected_course_group_id)
            potential_course_sites_query = potential_course_sites_query.filter(course__course_group=selected_course_group_id)
        # Filter potential_course_sites_query by department.
        elif selected_department_id and selected_department_id != '0':
            selected_department_id = int(selected_department_id)
            potential_course_sites_query = potential_course_sites_query.filter(course__department=selected_department_id)

    # TODO maybe better to use template tag unless used elsewhere?
    # TODO cont. this may be included in a summary generation to be displayed in page (see wireframe and Jira ticket)
    potential_course_site_count = (
        potential_course_sites_query.count() if potential_course_sites_query else 0
    )

    logger.debug(f'Retrieved {potential_course_site_count} potential course sites for term '
                 f'{selected_term_id}{logging_dept_cg_text}', extra={"sis_account_id": sis_account_id,
                                                                     "school_id": school_id,
                                                                     })

    context = {
        "terms": terms,
        "potential_course_sites": potential_course_sites_query,
        "potential_site_count": potential_course_site_count,
        "canvas_site_templates": canvas_site_templates,
        "departments": departments,
        "course_groups": course_groups,
        'selected_term_id': selected_term_id,
        'selected_course_group_id': selected_course_group_id,
        'selected_department_id': selected_department_id,
        'canvas_url': settings.CANVAS_URL,
    }
    return render(request, "bulk_site_creator/new_job.html", context=context)


@login_required
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(["POST"])
def create_bulk_job(request: HttpRequest) -> Optional[JsonResponse]:
    """
    This function creates the Bulk Site Creator jobs and
    redirects to the index view.
    """
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
    template_id = None if table_data['template'] == '0' else table_data['template']
    template_name = 'No template' if not template_id else get_canvas_site_template_name(template_id)

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
                course_group_id = int(course_group_id)
                course_group_name = CourseGroup.objects.get(course_group_id=course_group_id).name
                potential_course_sites_query = potential_course_sites_query.filter(course__course_group=course_group_id)
        else:
            if department_id and department_id != '0':
                department_id = int(department_id)
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

        log_extra = {
            'sis_account_id': sis_account_id,
            'user_id': user_id,
            'user_full_name': user_full_name,
            'user_email': user_email,
            'school': school_id,
            'term_id': term_id,
            'term_name': term_name,
            'department_id': department_id,
            'department_name': department_name,
            'course_group_id': course_group_id,
            'course_group_name': course_group_name,
            'template_id': template_id
        }
        # Sanitized input for log statements.
        term_id = str(term_id)
        sis_account_id = str(sis_account_id)
        logger.debug(f'Generating task objects for term ID {term_id} (term name {term_name}) '
                     f'and custom Canvas account sis ID {sis_account_id}.', extra=log_extra)

        # Create TaskRecord objects for each course instance
        tasks = generate_task_objects(potential_course_sites_query, job)

        # Set the bulk_processing field to true for all course instances being processed by this job so they
        # do not show up in the new job page
        potential_course_sites_query.update(bulk_processing=True)

        logger.debug(f'Creating bulk job for term ID {term_id} (term name {term_name}) '
                     f'and custom Canvas account sis ID {sis_account_id}.', extra=log_extra)
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

    logger.debug(f'Job creation process complete for term ID {term_id} (term name {term_name}) '
                 f'and custom Canvas account sis ID {sis_account_id}.', extra=log_extra)
    return redirect('bulk_site_creator:index')
