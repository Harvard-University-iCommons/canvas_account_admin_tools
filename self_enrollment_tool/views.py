import logging

from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods import courses
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import CourseInstance, SimplePerson, UserRole
from lti_permissions.decorators import lti_permission_required

from self_enrollment_tool.models import SelfEnrollmentCourse


logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def index(request):
    self_enroll_course_list = SelfEnrollmentCourse.objects.all()

    updater_ids = set()
    course_instance_ids = set()
    for course in self_enroll_course_list:
        updater_ids.add(course.updated_by)
        course_instance_ids.add(course.course_instance_id)

    self_enroll_course_list = _filter_launch_school_courses(
        request, self_enroll_course_list, course_instance_ids)

    # Update "updated_by" ids to full name and add other 
    # relevant data from course_info_updater (CourseInstance objects), etc..
    updaters = SimplePerson.objects.get_list_as_dict(user_ids=updater_ids)
    course_info = CourseInstance.objects.filter(course_instance_id__in=course_instance_ids)
    user_roles = UserRole.objects.all()

    for course in self_enroll_course_list:
        updater = updaters.get(course.updated_by)
        if updater:
            course.last_modified_by_full_name = f'{updater.name_first} {updater.name_last}'

        try:
            course_info_updater = course_info.get(course_instance_id=course.course_instance_id)
            if course_info_updater:
                course.course = course_info_updater.course
                course.section = course_info_updater.section
                course.term = course_info_updater.term
                course.title = course_info_updater.title
                course.short_title = course_info_updater.short_title
                course.sub_title = course_info_updater.sub_title
        except CourseInstance.DoesNotExist:
            logger.exception(f'This course instance ID {course.course_instance_id} '
                             f'does no exist in course instance database table')

        if course.role_id:
            course.role_name = user_roles.get(role_id=course.role_id).role_name

        course.self_enroll_url = _self_enroll_url(request, course.course_instance_id)

    context = {
        'self_enroll_course_list': self_enroll_course_list
    }
    return render(request, 'self_enrollment_tool/index.html', context=context)


def _filter_launch_school_courses(request, courses, course_instance_ids):
    """
    Create a subset of courses only containing courses from tool launch shool
    """
    # The school that this tool is being launched in
    tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]
    launch_school_crs_instance_ids = set()
    course_info = CourseInstance.objects.filter(course_instance_id__in=course_instance_ids)
    
    for course in courses:
        try:
            course_info_updater = course_info.get(course_instance_id=course.course_instance_id)
            if course_info_updater and course_info_updater.course.school_id == tool_launch_school:
                    launch_school_crs_instance_ids.add(course.course_instance_id)
        except CourseInstance.DoesNotExist:
            continue

    # Return subset of launch school self enroll courses
    return courses.filter(course_instance_id__in=launch_school_crs_instance_ids)


def _self_enroll_url(request, course_instance_id):
    """
    This function creates the self enroll course URL, then checks 
    if `?resource_link_id` is at the end of the url, then removes it 
    if exists.
    """
    self_enroll_url = request.build_absolute_uri(reverse(
        'self_enrollment_tool:enable', args=[course_instance_id]))

    if '?resource_link_id' in self_enroll_url:
        self_enroll_url = self_enroll_url[:self_enroll_url.rfind(
            '?resource_link_id')]

    return self_enroll_url
    

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
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
                    logger.error(f'Course instance ID ({course_search_term}) does not match Canvas course '
                                 f'SIS ID ({cc["sis_course_id"]}) for Canvas course {ci.canvas_course_id}. Aborting.')
                    messages.error(request, f'Course instance ID ({course_search_term}) does not match Canvas '
                                            f'course SIS ID ({cc["sis_course_id"]}) for Canvas course '
                                            f'{ci.canvas_course_id}. Aborting.')
                    context['abort'] = True

                # Check if it is an ILE or SB course. (source != xmlfeed)
                if ci.source == 'xmlfeed':
                    logger.error(f'Course instance ID ({course_search_term}) is not an ILE course. Aborting.')
                    messages.error(request, f'Course instance ID ({course_search_term}) is not an ILE/SB course.')
                    context['abort'] = True

                # Check if Self Enrollment record already exists for this course
                exists = SelfEnrollmentCourse.objects.filter(course_instance_id=ci.course_instance_id).exists()
                if exists:
                    logger.error(f'Self Enrollment is already enabled for this course  {ci.course_instance_id} ')
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
        role_names = set()
        # Role ID to role name
        user_roles = UserRole.objects.all()
        for role in roles:
            role_names.add(user_roles.get(role_id=role).role_name)

        context['roles'] = role_names

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
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
@require_http_methods(['GET', 'POST'])
def enable (request, course_instance_id):
    """
    Enable Self enrollment for the Course with the chosen role
    """
    logger.debug(request)
    role_id = request.POST.get('role_id')

    role_name = request.POST.get('role_name')
    logger.debug(f'Selected Role_id {role_id} (role_name {role_name}) for Self Enrollment in course {course_instance_id}')

    context = {
        'canvas_url': settings.CANVAS_URL,
        'course_instance_id' : course_instance_id,
        'role_id':role_id,
        'role_name': role_name,
        'abort': False,
    }
    
    try:
        if role_id and course_instance_id:
            # TODO: add validation to check if self enrollment si already enabled for this course
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
                context['enrollment_url'] = _self_enroll_url(request, course_instance_id)
    except Exception as e:
        message = 'Error creating self enrollment record  for course {} with role {} error details={}' \
            .format(course_instance_id, role_id, e)
        logger.exception(message)
        context['abort'] = True

    return render(request, 'self_enrollment_tool/enable_enrollment.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
@require_http_methods(['GET', 'POST'])
def enroll (request, course_instance_id):
    context = {
        'canvas_url': settings.CANVAS_URL,
        'course_instance_id' : course_instance_id,
        'abort': False,
    }
    return render(request, 'self_enrollment_tool/lookup.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def remove_self_enroll(request, pk):
    try:
        self_enrollment_course = SelfEnrollmentCourse.objects.get(pk=pk)
        self_enrollment_course.delete()
    except Exception as e:
        msg = f'Unable to remove self enrollment course {pk}.'
        logger.exception(msg)
        logger.exception(e)
        messages.error(request, msg)

    return redirect('self_enrollment_tool:index')
