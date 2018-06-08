import logging
import json
import time


from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import HttpResponse


from canvas_course_site_wizard.models import BulkCanvasCourseCreationJob, \
    CanvasCourseGenerationJob
from icommons_common.models import School, Term, Department, CourseGroup, Person
from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts

from lti_permissions.decorators import lti_permission_required
from lti_permissions.verification import get_school_sub_account_from_account_id

from .models import (
    get_course_instance_query_set,
    get_course_instance_summary_data,
    get_course_job_summary_data
)
from .utils import (
    get_term_data_for_school,
    get_department_data_for_school,
    get_course_group_data_for_school,
    get_term_data,
    get_canvas_site_templates_for_school,
    get_canvas_site_template
)


logger = logging.getLogger(__name__)

COURSE_INSTANCE_FILTERS = ['school', 'term', 'department', 'course_group']


def lti_auth_error(request):
    raise PermissionDenied


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def index(request):
    start_time = time.time()

    sis_account_id = request.LTI['custom_canvas_account_sis_id']
    ci_filters = {key: request.GET.get(key, '')
                  for key in COURSE_INSTANCE_FILTERS}
    (account_type, _) = canvas_api_accounts.parse_canvas_account_id(sis_account_id)
    schools = []
    terms = []
    departments = []
    course_groups = []
    school = None

    # Proceed only for valid account types
    if account_type in canvas_api_accounts.ACCOUNT_TYPES:

        # If user is in context Department or Course Group, display a
        # message conveying restricted access
        if (account_type == canvas_api_accounts.ACCOUNT_TYPE_DEPARTMENT or
            account_type == canvas_api_accounts.ACCOUNT_TYPE_COURSE_GROUP):
            return render(request, 'canvas_site_creator/restricted_access.html',
                          status=403)

        # We are in the context of a SIS type account, so limit options to that
        # context
        account = get_school_sub_account_from_account_id(sis_account_id)
        school = {'id': account.get('sis_account_id'),
                  'name': account.get('name')}

        ci_filters[canvas_api_accounts.ACCOUNT_TYPE_SCHOOL] = school['id']
        schools.append(school)

    # if schools size is zero(includes improperly formatted account_type),
    # display unauthorized message
    if len(schools) == 0:
        return redirect('not_authorized')
    if school:
        # Populate term, department, and course_group filter options if we already have a school
        school_sis_account_id = school['id']

        terms, current_term_id = get_term_data_for_school(school_sis_account_id)
        if current_term_id:
            ci_filters['term'] = current_term_id
        if not departments and not course_groups:
            departments = get_department_data_for_school(school_sis_account_id)
            course_groups = get_course_group_data_for_school(school_sis_account_id)
    context = {
        'course_groups': course_groups,
        'departments': departments,
        'filters': ci_filters,
        'in_school_account': (account_type ==
                                  canvas_api_accounts.ACCOUNT_TYPE_SCHOOL),
        'schools': schools,
        'terms': terms,
    }
    logger.debug(" --------->Initial load of the Site creator view took : %s seconds" % (time.time() - start_time))
    return render(request, 'canvas_site_creator/index.html', context)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def audit(request):
    canvas_user_id = request.LTI['custom_canvas_user_id']
    sis_account_id = request.LTI['custom_canvas_account_sis_id']
    (account_type, account_id) = canvas_api_accounts.parse_canvas_account_id(sis_account_id)

    filter_kwargs = {}
    if account_type == canvas_api_accounts.ACCOUNT_TYPE_SCHOOL:
        filter_kwargs['school_id'] = account_id
    elif account_type == canvas_api_accounts.ACCOUNT_TYPE_DEPARTMENT:
        filter_kwargs['sis_department_id'] = account_id
    elif account_type == canvas_api_accounts.ACCOUNT_TYPE_COURSE_GROUP:
        filter_kwargs['sis_course_group_id'] = account_id

    query_set = BulkCanvasCourseCreationJob.objects.filter(**filter_kwargs).order_by('-created_at')

    jobs = []
    creator_ids = set()
    school_ids = set()
    term_ids = set()
    department_ids = set()
    course_group_ids = set()
    for bulk_job in query_set:
        jobs.append(bulk_job)
        creator_ids.add(bulk_job.created_by_user_id)
        school_ids.add(bulk_job.school_id)
        term_ids.add(bulk_job.sis_term_id)
        if bulk_job.sis_department_id:
            department_ids.add(bulk_job.sis_department_id)
        if bulk_job.sis_course_group_id:
            course_group_ids.add(bulk_job.sis_course_group_id)

    creators = {p.univ_id: p for p in Person.objects.filter(univ_id__in=creator_ids)}
    schools = School.objects.in_bulk(school_ids)
    terms = Term.objects.in_bulk(term_ids)
    departments = {}
    if department_ids:
        departments = {
            id: name for id, name in Department.objects.filter(
                department_id__in=department_ids
            ).values_list('department_id', 'name')
        }
    course_groups = {}
    if course_group_ids:
        course_groups = {
            id: name for id, name in CourseGroup.objects.filter(
                course_group_id__in=course_group_ids
            ).values_list('course_group_id', 'name')
        }

    bulk_job_data = []
    for bulk_job in jobs:
        try:
            creator = creators[bulk_job.created_by_user_id]
            creator_name = "%s, %s" % (creator.name_last, creator.name_first)
        except KeyError:
            # Bulk job creator could not be found
            logger.warning("Failed to find bulk canvas site job creator %s", bulk_job.created_by_user_id)
            creator_name = ''

        school = schools[bulk_job.school_id]
        term = terms[bulk_job.sis_term_id]
        department = ''
        if bulk_job.sis_department_id:
            department = departments[bulk_job.sis_department_id]
        course_group = ''
        if bulk_job.sis_course_group_id:
            course_group = course_groups[bulk_job.sis_course_group_id]
        template_canvas_course = get_canvas_site_template(school.school_id, bulk_job.template_canvas_course_id)

        bulk_job_data.append({
            'id': bulk_job.id,
            'created_at': timezone.localtime(bulk_job.created_at).strftime('%b %d, %Y %H:%M:%S'),
            'status': bulk_job.status_display_name,
            'created_by': creator_name,
            'term': term.display_name,
            'school': school.title_short,
            'subaccount': department if department else course_group,
            'template_canvas_course': template_canvas_course,
            'count_course_jobs': CanvasCourseGenerationJob.objects.filter(bulk_job_id=bulk_job.id).count()
        })

    return render(request, 'canvas_site_creator/audit.html', {
        'bulk_job_data': bulk_job_data
    })


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def course_selection(request):
    ci_filters = {key: request.GET.get(key, '') for key in COURSE_INSTANCE_FILTERS}
    sis_account_id = request.LTI['custom_canvas_account_sis_id']
    start_time = time.time()

    # Fetch school data from DB instead of making api calls(causing timeouts for some users)
    try:
        school_id = sis_account_id.split(':')[1]
        school = School.objects.get(school_id=school_id)
        term = get_term_data(ci_filters['term'])
    except Exception as ex:
        logger.exception("Error retrieving school information for sis_account_id=%s" % sis_account_id)
        redirect('canvas_site_creator:index')
    canvas_site_templates = get_canvas_site_templates_for_school(school_id)

    account = None
    department = {}
    if ci_filters['department']:
        department = get_department_data_for_school(sis_account_id, ci_filters['department'])
        account = department
    course_group = {}
    if ci_filters['course_group']:
        course_group = get_course_group_data_for_school(sis_account_id, ci_filters['course_group'])
        account = course_group

    if account:
        ci_query_set = get_course_instance_query_set(term['id'], account['id'])
    else:
        # else pass in the school account id
        ci_query_set = get_course_instance_query_set(term['id'], sis_account_id)
    course_instance_summary = get_course_instance_summary_data(ci_query_set)

    logger.debug("\n\n--------->Initial load of the course_selection took : %s seconds" % (time.time() - start_time))
    return render(request, 'canvas_site_creator/course_selection.html', {
        'filters': ci_filters,
        'school': school,
        'term': term,
        'department': department,
        'course_group': course_group,
        'canvas_site_templates': canvas_site_templates,
        'course_instance_summary': course_instance_summary
    })


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def create_new_course(request):
    start_time = time.time()
    canvas_user_id = request.LTI['custom_canvas_user_id']
    sis_account_id = request.LTI['custom_canvas_account_sis_id']

    # Fetch school data from DB
    try:
        school_id = sis_account_id.split(':')[1]
        school = School.objects.get(school_id=school_id)
    except:
        logger.exception("Error retrieving school information for sis_account_id=%s" % sis_account_id)
        return HttpResponse(json.dumps({'error': 'retrieving school information for sis_account_id=%s' % sis_account_id}),
                            content_type="application/json", status=500)
    if not school:
        return render(request, 'canvas_site_creator/restricted_access.html',
                      status=403)

    canvas_site_templates = get_canvas_site_templates_for_school(school_id)

    logger.debug("\n\n--------->Initial load of the create_new_course view took : %s seconds" % (time.time() - start_time))
    return render(request, 'canvas_site_creator/create_new_course.html',
                  {'school_id': school_id, 'school_name': school.title_short,
                   'canvas_site_templates': canvas_site_templates})

@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'canvas_site_creator/partials/' + path, {})


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['POST'])
def create_job(request):
    canvas_user_id = request.LTI['custom_canvas_user_id']
    logged_in_user_id = request.LTI['lis_person_sourcedid']
    data = json.loads(request.POST['data'])

    template_canvas_course_id = data.get('template')
    filters = data['filters']
    term = filters.get('term')

    school_account_id = filters['school']
    (account_type, school_id) = canvas_api_accounts.parse_canvas_account_id(school_account_id)

    department = None
    department_account_id = filters.get('department')
    if department_account_id:
        (account_type, department) = department_account_id.split(':')

    course_group = None
    course_group_account_id = filters.get('course_group')
    if course_group_account_id:
        (account_type, course_group) = course_group_account_id.split(':')

    created_by_user_id = logged_in_user_id
    if not created_by_user_id:
        created_by_user_id = "canvas_user_id:%s" % canvas_user_id

    # If the create_all flag has been set and passed with the form,
    # then create a query to get the all course instances with the applied filters that are to be created.
    course_instance_ids = []
    if data.get('create_all', False):
        # Get the account data to be used in the course instance query.
        if filters['course_group']:
            account = filters['course_group']
        elif filters['department']:
            account = filters['department']
        else:
            account = filters['school']

        # Retrieve all course instances for the given term and account that do not have Canvas course sites.
        ci_query_set_without_canvas = get_course_instance_query_set(term, account).filter(canvas_course_id__isnull=True)

        # Iterate through the query set to build a list of all the course instance id's
        # for a school/course_group/department, which course sites will be created for.
        for ci in ci_query_set_without_canvas:
            course_instance_ids.append(ci.course_instance_id)
    else:
        course_instance_ids = data['course_instance_ids']

    create_bulk_job_kwargs = {
        'school_id': school_id,
        'sis_term_id': int(term),
        'sis_department_id': int(department) if department else None,
        'sis_course_group_id': int(course_group) if course_group else None,
        'template_canvas_course_id': template_canvas_course_id,
        'created_by_user_id': created_by_user_id,
        'course_instance_ids': course_instance_ids
    }

    bulk_job = BulkCanvasCourseCreationJob.objects.create_bulk_job(**create_bulk_job_kwargs)

    return redirect('canvas_site_creator:bulk_job_detail', bulk_job.id)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def bulk_job_detail(request, bulk_job_id):
    bulk_job = BulkCanvasCourseCreationJob.objects.get(id=bulk_job_id)
    bulk_job_complete = bulk_job.status in (
        BulkCanvasCourseCreationJob.STATUS_NOTIFICATION_SUCCESSFUL,
        BulkCanvasCourseCreationJob.STATUS_NOTIFICATION_FAILED
    )
    course_job_summary = get_course_job_summary_data(bulk_job.id)

    school = School.objects.get(school_id=bulk_job.school_id)
    term = Term.objects.get(term_id=bulk_job.sis_term_id)

    department = None
    if bulk_job.sis_department_id:
        department = Department.objects.get(department_id=bulk_job.sis_department_id).name

    course_group = None
    if bulk_job.sis_course_group_id:
        course_group = CourseGroup.objects.get(course_group_id=bulk_job.sis_course_group_id).name

    template = get_canvas_site_template(school.school_id, bulk_job.template_canvas_course_id)

    return render(request, 'canvas_site_creator/bulk_job_detail.html', {
        'bulk_job': bulk_job,
        'bulk_job_complete': bulk_job_complete,
        'school': school.title_short,
        'term': term.display_name,
        'department': department,
        'course_group': course_group,
        'template': template,
        'course_jobs_total': course_job_summary['recordsTotal'],
        'course_jobs_complete': course_job_summary['recordsComplete'],
        'course_jobs_successful': course_job_summary['recordsSuccessful'],
        'course_jobs_failed': course_job_summary['recordsFailed']
    })
