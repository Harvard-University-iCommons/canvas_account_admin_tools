import logging
from ast import literal_eval
from uuid import uuid4

from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods import courses
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_utils import (SessionInactivityExpirationRC,
                                          add_canvas_course_enrollee,
                                          add_canvas_section_enrollee,
                                          get_canvas_course_by_canvas_id,
                                          get_canvas_course_section,
                                          get_canvas_enrollment_by_user,
                                          get_canvas_user)
from icommons_common.models import (CourseEnrollee, CourseInstance,
                                    DeletedEnrollee, SimplePerson, UserRole)
from lti_permissions.decorators import lti_permission_required

from self_enrollment_tool.models import SelfEnrollmentCourse

from .utils import get_canvas_roles

logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def index(request):
    try:
        # The school that this tool is being launched in
        tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]
    except Exception:
        logger.exception('Error getting launch school')

    # Self-enroll course instance IDs
    course_instance_ids = {
        crs_id[0] for crs_id in SelfEnrollmentCourse.objects.values_list('course_instance_id')}

    # Additional course info for the tool launch school courses
    course_info = CourseInstance.objects.filter(
        course_instance_id__in=course_instance_ids, course__school=tool_launch_school)

    # Tool launch school course instance IDs
    course_instance_ids = {crs_id[0] for crs_id in course_info.values_list('course_instance_id')}

    self_enroll_course_list = SelfEnrollmentCourse.objects.filter(
        course_instance_id__in=course_instance_ids)

    # Update "updated_by" ids to first and last name and add other
    # relevant data from course_info_updater (CourseInstance objects), etc..
    updater_ids = {course.updated_by for course in  self_enroll_course_list}
    updaters = SimplePerson.objects.get_list_as_dict(user_ids=updater_ids)
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

        self_enroll_url = request.build_absolute_uri(
            reverse('self_enrollment_tool:enable', args=[course.course_instance_id]))

        course.self_enroll_url = _self_enroll_url(self_enroll_url)

    context = {
        'self_enroll_course_list': self_enroll_course_list
    }
    return render(request, 'self_enrollment_tool/index.html', context=context)


def _self_enroll_url(self_enroll_url):
    """
    This function checks if `?resource_link_id` is at
    the end of the url, then removes it if exists.
    """
    if '?resource_link_id' in self_enroll_url:
        self_enroll_url = self_enroll_url[:self_enroll_url.rfind(
            '?resource_link_id')]

    return self_enroll_url


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
                    logger.error(f'Course instance ID ({course_search_term}) does not match Canvas course '
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
        context['roles'] = get_canvas_roles()

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
@require_http_methods(['POST'])
def enable (request, course_instance_id):
    """
    Enable Self enrollment for the Course with the chosen role
    """
    logger.debug(request)

    roles = literal_eval(request.POST.get('roles'))
    role_id = roles.get('roleId', '')
    role_name = roles.get('roleName', '')
    logger.debug(f'Selected role_name {role_name} with role_id {role_id} for Self Enrollment in course {course_instance_id}')

    context = {
        'canvas_url': settings.CANVAS_URL,
        'course_instance_id' : course_instance_id,
        'role_id':role_id,
        'role_name': role_name,
        'abort': False,
    }

    try:
        if role_id and course_instance_id:
            try:
                course_instance = SelfEnrollmentCourse.objects.get(course_instance_id=course_instance_id, role_id=role_id)
                logger.error(f'Self Enrollment is already enabled for this course  {course_instance_id} ')
                messages.error(request, f'Self Enrollment is already enabled for this course {course_instance_id}')
                path = reverse('self_enrollment_tool:enroll', args=[course_instance.uuid])
                context['abort'] = True
            except SelfEnrollmentCourse.DoesNotExist:
                uuid = str(uuid4())
                SelfEnrollmentCourse.objects.create(course_instance_id=course_instance_id,
                                              role_id=role_id,
                                              updated_by=str(request.user),
                                              uuid=uuid)
                path = reverse('self_enrollment_tool:enroll', args=[uuid])
                logger.debug(f'Successfully saved Role_id {role_id} for Self Enrollment in course {course_instance_id}. UUID={uuid}')
                messages.success(request, f"Successfully enabled Self Enrollment for SIS Course Id"
                                          f" {course_instance_id} for role {role_name}")
    except Exception as e:
        message = 'Error creating self enrollment record  for course {} with role {} error details={}' \
            .format(course_instance_id, role_id, e)
        logger.exception(message)
        context['abort'] = True
        return render(request, 'self_enrollment_tool/enable_enrollment.html', context)

    context['enrollment_url'] = f'{request.scheme}://{request.get_host()}{path}'
    return render(request, 'self_enrollment_tool/enable_enrollment.html', context)


@login_required
def enroll (request, uuid):
    # verify that the specified uuid corresponds to an existing self-reg course
    try:
        self_reg_course = SelfEnrollmentCourse.objects.get(uuid=uuid)
    except SelfEnrollmentCourse.DoesNotExist:
        logger.warn(
            f"A user is trying to self-reg for course with uuid={uuid}, but no such "
            f"record exists with this uuid."
        )
        return render(request, 'self_enrollment_tool/error.html', {'message': 'Sorry, this course has not been setup for self-registration.'})

    # store various pieces of data for subsequent reference
    course_instance_id = self_reg_course.course_instance_id
    course_instance = CourseInstance.objects.get(course_instance_id=course_instance_id)
    canvas_course_id = course_instance.canvas_course_id
    course_url = '%s/courses/%s' % (settings.CANVAS_URL, canvas_course_id)
    canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)

    # is the user already in the course?
    user_id = request.user.username
    is_enrolled = False
    enrollments = get_canvas_enrollment_by_user('sis_user_id:%s' % user_id)
    if enrollments:
        for e in enrollments:
            logger.debug(
                'user %s is enrolled in %d - checking against %s' % (user_id, e['course_id'], canvas_course_id))
            if e['course_id'] == int(canvas_course_id):
                is_enrolled = True
                break

    if is_enrolled is True:
        # redirect the user to the actual canvas course site
        logger.info('User %s is already enrolled in course %s - redirecting to site.' % (user_id, canvas_course_id))
        return redirect(course_url)

    # make sure the user has a Canvas account
    canvas_user = get_canvas_user(user_id)
    if not canvas_user:
        return render(request, 'self_enrollment_tool/error.html', {'message': 'Sorry, there was a problem enrolling you in this course.'})

    # Enroll this user with the mapped role
    # if there is a section matching the course's sis_course_id,
    # enroll the user in that; otherwise use the default section
    user_role = UserRole.objects.get(role_id=self_reg_course.role_id)
    canvas_role = user_role.canvas_role
    canvas_role_id = user_role.canvas_role_id
    if canvas_course.get('sis_course_id'):
        canvas_section = get_canvas_course_section(canvas_course['sis_course_id'])
        if canvas_section:
            new_enrollee = add_canvas_section_enrollee(canvas_section['id'], canvas_role, user_id, enrollment_role_id=canvas_role_id)
        else:
            new_enrollee = add_canvas_course_enrollee(canvas_course_id, canvas_role, user_id, enrollment_role_id=canvas_role_id)
    else:
        new_enrollee = add_canvas_course_enrollee(canvas_course_id, canvas_role, user_id, enrollment_role_id=canvas_role_id)

    if new_enrollee:
        # success
        return redirect(course_url)
    else:
        return render(request, 'self_enrollment_tool/error.html', {'message': 'Sorry, there was a problem enrolling you in this course.'})


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['DELETE'])
def disable(request, pk):
    """
    Removes course from self enrollment table.
    Users will no longer be able to self enroll in course.
    """
    logger.info(f'Deleting self-enroll course pk:{pk}.')

    try:
        try:
            self_enrollment_course = SelfEnrollmentCourse.objects.get(pk=pk)
        except SelfEnrollmentCourse.DoesNotExist:
            msg = f'Course (pk:{pk}) does not exists and therefore cannot be deleted.'
            logger.warning(msg)
            messages.warning(request, msg)

        self_enrollment_course.delete()
    except Exception:
        msg = f'Unable to delete self-enroll course pk:{pk}.'
        logger.exception(msg)
        messages.error(request, msg)

    logger.info(f'Deleted self-enroll course pk:{pk}.')
    return redirect('self_enrollment_tool:index')


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['DELETE'])
def unenroll_user_from_course(request, course_instance_id, user_id):
    """
    This functions deletes a user from a self-enroll course.
    """
    logger.info(
        f'Deleting user_id:{user_id} from self-enroll course_instance_id:{course_instance_id}.')

    try:
        try:
            course_enrollee = CourseEnrollee(
                user_id=user_id, course_instance_id=course_instance_id)
        except CourseEnrollee.DoesNotExist:
            msg = f'user_id:{user_id} enrolled in course_instance_id:{course_instance_id} '
            f'does not exists and therefore cannot be deleted.'
            logger.warning(msg)
            messages.warning(request, msg)

        # TODO: Add code to delete or archive course enrollee record.
        # course_enrollee.DeletedEnrollee()
    except Exception:
        msg = f'Unable to delete user_id:{user_id} from course_instance_id:{course_instance_id}.'
        logger.exception(msg)
        messages.error(request, msg)

    logger.info(
        f'Deleted user_id:{user_id} from self-enroll course_instance_id:{course_instance_id}.')

    return redirect('self_enrollment_tool:index')  # TODO: Change this, we don't want to redirect to this page
