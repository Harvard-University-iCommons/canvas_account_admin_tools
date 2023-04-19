import json
import logging

from canvas_api.helpers import accounts as canvas_api_accounts
from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.content_migrations import \
    create_content_migration_courses
from canvas_sdk.methods.courses import create_new_course, update_course
from canvas_sdk.methods.sections import create_course_section
from coursemanager.models import CourseInstance
from coursemanager.people_models import Person
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from lti_school_permissions.decorators import lti_permission_required

from .models import (get_course_instance_query_set,
                     get_course_instance_summary_data,
                     get_course_job_summary_data)
from common.utils import (get_course_group_data_for_school,
                    get_department_data_for_school,
                    get_school_data_for_sis_account_id,
                    get_term_data_for_school)

logger = logging.getLogger(__name__)

COURSE_INSTANCE_DATA_FIELDS = ('course_instance_id', 'course_instance_id',
                               'course__registrar_code_display','title',
                               'section')
BULK_JOB_DATA_FIELDS = ('created_at', 'status')
COURSE_JOB_DATA_FIELDS = ('created_at', 'workflow_state')

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)


def _unpack_datatables_params(request):
    return (
        int(request.GET.get('draw', 0)),
        int(request.GET.get('start', 0)),
        int(request.GET.get('length', 10)),
        int(request.GET.get('order[0][column]', 3)),
        request.GET.get('order[0][dir]', 'asc'),
        request.GET.get('search[value]')
    )




@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def schools(request):
    """
    Gets the list of schools that the current user has permission to manage

    :param request:
    :return: JSON response containing the list of schools
    """

    try:
        data = get_school_data_for_sis_account_id(
            request.LTI['custom_canvas_account_sis_id'])
        return JsonResponse(data)
    except Exception:
        message = "Failed to get schools with Canvas account_sis_id %s"\
                  % request.LTI['custom_canvas_account_sis_id']
        logger.exception(message)
        return JsonResponse({'error': message}, status=500)



@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def terms(request, sis_account_id):
    """
    Gets the list of terms for a given school

    :param request:
    :param sis_account_id: The sis_account_id for which to find terms
    :return: JSON response containing the list of terms
    """
    try:
        data, _ = get_term_data_for_school(sis_account_id)
        return JsonResponse(data)
    except Exception:
        message = "Failed to get terms with sis_account_id %s" % sis_account_id
        logger.exception(message)
        return JsonResponse({'error': message}, status=500)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def departments(request, sis_account_id):
    """
    Gets the list of departments that the current user has permission to manage

    :param request:
    :param sis_account_id: The sis_account_id for which to find departments
    :return: JSON response containing the list of departments
    """
    try:
        data = get_department_data_for_school(sis_account_id)
        return JsonResponse(data)
    except Exception:
        message = "Failed to get departments with sis_account_id %s" % sis_account_id
        logger.exception(message)
        return JsonResponse({'error': message}, status=500)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def course_groups(request, sis_account_id):
    """
    Gets the list of course_groups that the current user has permission to manage

    :param request:
    :param sis_account_id: The sis_account_id for which to find course_groups
    :return: JSON response containing the list of course_groups
    """
    try:
        data = get_course_group_data_for_school(request.LTI['custom_canvas_user_id'], sis_account_id)
        return JsonResponse(data)
    except Exception:
        message = "Failed to get course groups with sis_account_id %s" % sis_account_id
        logger.exception(message)
        return JsonResponse({'error': message}, status=500)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['POST'])
def create_canvas_course_and_section(request):

    try:
        data = json.loads(request.body)
        is_blueprint = data['is_blueprint']
        # If this is a blueprint course, create course at school level not in the ILE sub account
        account_id = 'sis_account_id:%s' % (data['school_id'] if is_blueprint else data['dept_id'])
        # not using .get() default because we want to fall back on course_code
        # if short_title is an empty string
        course_code = data.get('short_title', '').strip() or data['course_code']
        course_instance_id = data['course_instance_id']
        school = data['school']
        section_id = data['section_id']
        term_id = 'sis_term_id:%s' % data['term_id']
        title = data['title']
    except Exception:
        message = ('Failed to extract canvas parameters from posted data; '
                   'request body={}'.format(request.body))
        logger.exception(message)
        return JsonResponse({'error': message}, status=400)

    request_parameters = dict(
        request_ctx=SDK_CONTEXT,
        account_id=account_id,
        course_course_code=course_code,
        course_name=title,
        course_sis_course_id=course_instance_id,
        course_term_id=term_id
    )

    try:
        course_result = create_new_course(**request_parameters).json()

        # If this course is meant to be a blueprint course,
        # the newly created course needs to have its blueprint field set to True
        if is_blueprint:
            update_parameters = dict(
                request_ctx=SDK_CONTEXT,
                id=course_result['id'],
                course_blueprint=True
            )
            try:
                update_course(**update_parameters).json()
            except:
                logger.exception("Error creating blueprint course via update with request {}".format(update_parameters))
                return JsonResponse({}, status=500)
    except Exception as e:
        message = 'Error creating new course via SDK with request={}'.format(
            request_parameters)
        if isinstance(e, CanvasAPIError):
            message += ', SDK error details={}'.format(e)
        logger.exception(message)
        return JsonResponse({}, status=500)

    # create the canvas section
    section_result = {}
    request_parameters = {}
    try:
        # format section name similar to how it is handled in the bulk feed :
        #  school + short title/course_code  + section id

        section_name = '{} {} {}'.format(school.upper(), course_code,
                                          section_id)
        request_parameters = dict(
            request_ctx=SDK_CONTEXT,
            course_id=course_result['id'],
            course_section_name=section_name,
            course_section_sis_section_id=course_instance_id)
        section_result = create_course_section(**request_parameters).json()
    except Exception as e:
        message = ('Error creating section for new course via SDK with '
                   'request={}'.format(request_parameters))
        if isinstance(e, CanvasAPIError):
            message += ', SDK error details={}'.format(e)
        logger.exception(message)
        return JsonResponse(section_result, status=500)

    return JsonResponse(course_result, status=200)

@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['POST'])
def copy_from_canvas_template(request):
    try:
        data = json.loads(request.body)
        canvas_course_id = data['canvas_course_id']
        template_id = data['template_id']
    except Exception:
        message = ('Failed to extract canvas parameters from posted data; '
                   'request body={}'.format(request.body))
        logger.exception(message)
        return JsonResponse({'error': message}, status=400)

    request_parameters = dict(request_ctx=SDK_CONTEXT,
                              course_id=canvas_course_id,
                              migration_type='course_copy_importer',
                              settings_source_course_id=template_id,
    )
    try:
        migration_result = create_content_migration_courses(
            **request_parameters).json()
        logger.debug('content migration API call result: %s' % migration_result)

    except Exception as e:
        message = 'Error creating content migration via SDK with request={}'\
            .format(request_parameters)
        if isinstance(e, CanvasAPIError):
            message += ', SDK error details={}'.format(e)
        logger.exception(message)
        return JsonResponse({}, status=500)
    return JsonResponse(migration_result, status=200)

@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def course_instances(request, sis_term_id, sis_account_id):
    """
    Searches for course instances using the GET parameters given

    :param request:
    :param sis_term_id: The SIS term to find course instances for
    :param sis_account_id: The Canvas account ID for the school to find course instances for
    :return: JSON response containing the list of course instances
    """
    result = {}
    try:
        (draw, start, limit, sort_index, sort_dir, search) = _unpack_datatables_params(request)

        query_set = get_course_instance_query_set(sis_term_id, sis_account_id)
        query_set = query_set.select_related('course')

        # Apply text search filter
        if search:
            query_set = query_set.filter(
                Q(course_instance_id__contains=search) |
                Q(course__registrar_code__icontains=search) |
                Q(course__registrar_code_display__icontains=search) |
                Q(title__icontains=search)
            )

        order_by_operator = '-' if sort_dir == 'desc' else ''
        query_set = query_set.order_by(order_by_operator + COURSE_INSTANCE_DATA_FIELDS[sort_index])

        # Exclude courses that are automatically fed to Canvas and already have a Canvas site
        query_set = query_set.exclude(sync_to_canvas=1).exclude(canvas_course_id__isnull=False)
        result = get_course_instance_summary_data(query_set)

        data = []
        for ci in query_set[start:(start + limit)]:
            data.append({
                'id': ci.course_instance_id,
                'registrar_code': ci.course.registrar_code_display or
                                  ci.course.registrar_code,
                'title': ci.title,
                'course_section': ci.section,
                'has_canvas_site': ci.canvas_course_id is not None,
            })

        result['data'] = data
        result['draw'] = draw
    except Exception:
        logger.exception(
            "Failed to get course_instances with LTI params %s and GET params %s",
            json.dumps(request.LTI),
            json.dumps(request.GET)
        )
        result['error'] = 'There was a problem searching for courses. Please try again.'
        return JsonResponse({'error': result}, status=500)

    return JsonResponse(result, status=200, content_type='application/json')


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def course_instance_summary(request, sis_term_id, sis_account_id):
    """
    Return counts of course instances using the GET parameters given

    :param request:
    :param sis_term_id: The SIS term to count course instances for
    :param sis_account_id: The Canvas account ID for the school to count course instances for
    :return: JSON response containing the course instance counts
    """
    result = {}
    try:
        query_set = get_course_instance_query_set(sis_term_id, sis_account_id)
        result = get_course_instance_summary_data(query_set)
    except Exception:
        logger.exception(
            "Failed to get course_instance_summary with LTI params %s and GET params %s",
            json.dumps(request.LTI),
            json.dumps(request.GET)
        )
        result['error'] = 'There was a problem counting courses. Please try again.'
        return JsonResponse({'error': result}, status=500)

    return JsonResponse(result)
