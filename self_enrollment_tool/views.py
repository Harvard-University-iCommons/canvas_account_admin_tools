from django.shortcuts import render

import logging

from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods import courses
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import CourseInstance
from lti_permissions.decorators import lti_permission_required
from self_enrollment_tool.models import SelfEnrollmentCourse


logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def index(request):
    context = {}
    return render(request, 'self_enrollment_tool/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET', 'POST'])
def lookup(request):
    course_search_term = request.POST.get('course_search_term')
    course_search_term = course_search_term.strip()
    context = {
        'canvas_url': settings.CANVAS_URL,
        'abort': False,
    }

    if course_search_term.isnumeric():
        try:
            ci = CourseInstance.objects.get(course_instance_id=course_search_term)
            context['course_instance'] = ci

            if ci.canvas_course_id:
                # get the Canvas course and make sure that the SIS ID matches
                response = courses.get_single_course_courses(SDK_CONTEXT, id=ci.canvas_course_id)
                if response.status_code == 200:
                    cc = response.json()
                else:
                    logger.error(f'Could not retrieve Canvas course {ci.canvas_course_id}')
                    messages.error(request, f'Could not find Canvas course {ci.canvas_course_id}')
                    context['abort'] = True

                if ci.course_instance_id != int(cc['sis_course_id']):
                    logger.warning(f'Course instance ID ({course_search_term}) does not match Canvas course '
                                 f'SIS ID ({cc["sis_course_id"]}) for Canvas course {ci.canvas_course_id}. Aborting.')
                    messages.error(request, f'Course instance ID ({course_search_term}) does not match Canvas '
                                            f'course SIS ID ({cc["sis_course_id"]}) for Canvas course '
                                            f'{ci.canvas_course_id}. Aborting.')
                    context['abort'] = True

                # Check if it is an ILE or SB course. (source != xmlfeed)
                if ci.source == 'xmlfeed':
                    logger.warning(f'Course instance ID ({course_search_term}) is not an ILE course. Aborting.')
                    messages.error(request, f'Course instance ID ({course_search_term}) is not an ILE/SB course.')
                    context['abort'] = True

                # Check if Self Enrollment record already exists for this course
                exists = SelfEnrollmentCourse.objects.filter(course_instance_id=ci.course_instance_id).exists()
                if exists:
                    logger.warning(f'Self Enrollment is already enabled for this course  {ci.course_instance_id} ')
                    messages.error(request, f'Self Enrollment is already enabled for this course {ci.course_instance_id} ')
                    context['abort'] = True
            else:
                logger.error(f'Course instance {ci.course_instance_id} does not have a Canvas course ID set.')
                messages.error(request, f'Course instance {ci.course_instance_id} does not have a Canvas course ID set. Cannot continue.')
                context['abort'] = True

        except CourseInstance.DoesNotExist:
            logger.exception('Could not determine the course instance for Canvas '
                             'course instance id %s' % course_search_term)
            messages.error(request, 'Could not find a Course Instance from search term')
            context['abort'] = True
        except CanvasAPIError:
            logger.exception(f'Could not find Canvas course {ci.canvas_course_id} via Canvas API')
            messages.error(request, f'Could not find Canvas course {ci.canvas_course_id}. Aborting.')
            context['abort'] = True
    else:
        messages.error(request, 'Search term must be populated and may only be numbers')

    # fetch the roles for the dropdown
    roles = settings.SELF_ENROLLMENT_TOOL_ROLES_LIST

    if roles:
        # todo : Get role names from role table and display role names in dropdown (currently role_ids are being shown)
        # This seems to have been done in 4279 by. Validate after merge and remove this todo
        context['roles'] = roles

    return render(request, 'self_enrollment_tool/add_new.html', context)

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def add_new(request):
    context = {}
    return render(request, 'self_enrollment_tool/add_new.html', context)

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET', 'POST'])
def enable (request, course_instance_id):
    """
    Enable Self enrollment for the Course with the chosen role
    """
    logger.debug(request)
    role_id = request.POST.get('role_id')

    # todo: retrive role name. Note: Thsi is implemented in teh other story for thsi tool but will remove this comment
    #  after verifying on merging upstream
    role_name = request.POST.get('role_id')
    logger.debug(f'Selected Role_id {role_id} for Self Enrollment in  course {course_instance_id}')

    context = {
        'canvas_url': settings.CANVAS_URL,
        'course_instance_id' : course_instance_id,
        'role_id':role_id,
        'role_name': role_name,
        'abort': False,
    }
    try:
        if role_id and course_instance_id:

            # check if self enrollment is already enabled for this course
            exists  = SelfEnrollmentCourse.objects.filter(course_instance_id=course_instance_id).exists()
            if exists :
                logger.error(f'Self Enrollment is already enabled for this course  {course_instance_id} ')
                messages.error(request, f'Self Enrollment is already enabled for this course {course_instance_id} ')
                context['abort'] = True
            else:
                new_self_enrollment_course = SelfEnrollmentCourse.objects.create(course_instance_id=course_instance_id,
                                              role_id=role_id,
                                              updated_by=str(request.user))
                logger.debug(f'Successfully saved Role_id {role_id} for Self Enrollment in course {course_instance_id}')
                messages.success(request, f"Successfully enabled Self Enrollment for SIS Course Id"
                                          f" {course_instance_id} for role {role_name}")

                # todo : format the Distributable Self reg link (this is related to tlt-4278) .
                enrollment_url = 'canvas_account_admin_tools/self_enrollment_tool/enroll/' + course_instance_id;
                context['enrollment_url'] = enrollment_url
    except Exception as e:
        message = 'Error creating self enrollment record  for course {} with role {} error details={}' \
            .format(course_instance_id, role_id, e)
        logger.exception(message)
        context['abort'] = True


    return render(request, 'self_enrollment_tool/enable_enrollment.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def enroll (request, course_instance_id):
    context = {
        'canvas_url': settings.CANVAS_URL,
        'course_instance_id' : course_instance_id,
        'abort': False,
    }
    return render(request, 'self_enrollment_tool/lookup.html', context)
