import json
import logging

from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.content_migrations import \
    create_content_migration_courses
from canvas_sdk.methods.courses import create_new_course, update_course
from canvas_sdk.methods.sections import create_course_section
from coursemanager.models import CourseInstance
from django.conf import settings
from django.http import JsonResponse

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


def get_course_instance_query_set(sis_term_id, sis_account_id):
    # Exclude records that have parent_course_instance_id  set(TLT-3558) as we don't want to create sites for the
    # children; they will be associated with the parent site
    filters = {'exclude_from_isites': 0, 'term_id': sis_term_id, 'parent_course_instance_id__isnull': True}

    (account_type, account_id) = sis_account_id.split(':')
    if account_type == 'school':
        filters['course__school'] = account_id
    elif account_type == 'dept':
        filters['course__department'] = account_id
    elif account_type == 'coursegroup':
        filters['course__course_group'] = account_id

    return CourseInstance.objects.filter(**filters)


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

        section_name = '{} {} {}'.format(school.upper(), course_code, section_id)
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
        migration_result = create_content_migration_courses(**request_parameters).json()
        logger.debug('content migration API call result: %s' % migration_result)

    except Exception as e:
        message = 'Error creating content migration via SDK with request={}'\
            .format(request_parameters)
        if isinstance(e, CanvasAPIError):
            message += ', SDK error details={}'.format(e)
        logger.exception(message)
        return JsonResponse({}, status=500)
    return JsonResponse(migration_result, status=200)
