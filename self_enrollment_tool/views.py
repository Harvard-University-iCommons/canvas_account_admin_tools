import logging
import datetime
import pytz
from ast import literal_eval
from uuid import uuid4

from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods import courses
from coursemanager.models import CourseInstance, UserRole
from coursemanager.people_models import SimplePerson
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from django.utils import timezone
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required

from self_enrollment_tool.models import SelfEnrollmentCourse

from .utils import get_canvas_roles, install_unenrollment_tool

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)


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
        course_instance_id__in=course_instance_ids).order_by('-last_updated')

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

        course.self_enroll_url = f'https://{settings.SELF_ENROLL_HOSTNAME}/{course.uuid}'

    context = {
        'self_enroll_course_list': self_enroll_course_list
    }
    return render(request, 'self_enrollment_tool/index.html', context=context)


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
        'course_instance': None,
    }

    if course_search_term.isnumeric():
        tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]
        try:
            ci = CourseInstance.objects.get(course_instance_id=course_search_term, course__school=tool_launch_school)
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
                    return render(request, 'self_enrollment_tool/add_new.html', context)

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
            logger.exception(f'Could not find Canvas course {course_search_term} via Canvas API')
            messages.error(request, f'Could not find Canvas course {course_search_term}. Aborting.')
            context['abort'] = True
    else:
        logger.warning(f'course search term {course_search_term} not numeric.')
        messages.error(request, 'Search term must be populated and may only be numbers')
        context['abort'] = True

    # fetch the roles for the dropdown
    roles = get_canvas_roles()
    if roles:
        context['roles'] = roles
    else:
        logger.error(f'Unable to retrieve roles for Canvas course {course_search_term}. Response from get_canvas_roles={roles}')
        messages.error(request, f'Error fetching roles for SIS ID {course_search_term}. Aborting.')
        context['abort'] = True

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
def enable(request, course_instance_id):
    """
    Enable Self enrollment for the Course with the chosen role
    """
    logger.debug(request)

    roles = literal_eval(request.POST.get('roles'))
    role_id = roles.get('roleId', '')
    role_name = roles.get('roleName', '')
    start_date_str = request.POST.get('start_date', None)
    end_date_str = request.POST.get('end_date', None)

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    eastern = pytz.timezone('US/Eastern')

    if start_date:
        start_date = eastern.localize(datetime.datetime.combine(start_date, datetime.time.min))
    if end_date:
        end_date = eastern.localize(datetime.datetime.combine(end_date, datetime.time.min))

    now_est = timezone.now().astimezone(eastern)
    today_start_est = eastern.localize(datetime.datetime.combine(now_est.date(), datetime.time.min))

    if start_date and start_date < today_start_est:
        messages.error(request, "Start date cannot be in the past.")
        return redirect('self_enrollment_tool:add_new')

    if end_date and end_date < now_est:
        messages.error(request, "End date must be in the future.")
        return redirect('self_enrollment_tool:add_new')

    if start_date and end_date and end_date < start_date:
        messages.error(request, "End date cannot be before the start date.")
        return redirect('self_enrollment_tool:add_new')
    
    try:
        if str(role_id) and course_instance_id:
            try:
                course_instance = SelfEnrollmentCourse.objects.get(
                    course_instance_id=course_instance_id, 
                    role_id=role_id, 
                    start_date__isnull=True,
                    end_date__isnull=True
                )
                logger.info(f'Self Enrollment is already enabled for this course  {course_instance_id} ')
                messages.error(request, f'Self Enrollment is already enabled for this course (SIS ID {course_instance_id}) and role ({role_name}). '
                              f'See below for the previously-generated link.')
                path = reverse('self_enrollment_tool:enroll', args=[course_instance.uuid])
            except SelfEnrollmentCourse.DoesNotExist:
                uuid = str(uuid4())
                SelfEnrollmentCourse.objects.create(
                    course_instance_id=course_instance_id,
                    role_id=role_id,
                    updated_by=str(request.user),
                    uuid=uuid,
                    start_date=start_date,
                    end_date=end_date
                )
                logger.info(f'Successfully saved Role_id {role_id} for Self Enrollment in course {course_instance_id}. UUID={uuid}')
                messages.success(request, f"Generated self-registration link. See details below.")

            # install the self-unenroll tool
            self_unenroll_client_id = settings.SELF_UNENROLL_CLIENT_ID
            try:
                result = install_unenrollment_tool(course_instance_id=course_instance_id, client_id=self_unenroll_client_id)
                if result == 'installed':
                    messages.success(request, f'Successfully installed self-unenrollment tool into the Canvas course.')
                elif result == 'already_installed':
                    messages.success(request, f'Self-Unenrollment tool already installed into the Canvas course.')
            except Exception as e:
                messages.warning(request, f'There was a problem installing the self-unenrollment tool into the Canvas course: {e}')

        else:
            message = f'One of role_id or course_instance_id not supplied in self-reg request. ci_id={course_instance_id}, role_id={role_id}'
            logger.exception(message)
            messages.error(request, message=message)
    except Exception as e:
        message = f'Error creating self enrollment record for course {course_instance_id} with role {role_id}. Error details={e}'
        logger.exception(message)
        messages.error(request, message=message)

    return redirect('self_enrollment_tool:index')


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_SELF_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def disable(request, uuid):
    """
    Removes course from self enrollment table.
    Users will no longer be able to self enroll in course.
    """
    context = {'uuid': uuid}
    logger.info(f'Deleting self-enroll URL for course uuid:{uuid}.', extra=context)

    try:
        try:
            self_enrollment_course = SelfEnrollmentCourse.objects.get(uuid=uuid)
        except SelfEnrollmentCourse.DoesNotExist:
            msg = f'Self-enroll URL for course does not exists and therefore cannot be deleted.'
            logger.warning(msg, extra=context)
            messages.warning(request, msg)

        self_enrollment_course.delete()
    except Exception:
        msg = f'Unable to delete self-enroll URL for course.'
        logger.exception(msg, extra=context)
        messages.error(request, msg)

    msg = f'Successfully deleted self-enroll URL for course.'
    logger.info(msg, extra=context)
    messages.success(request, msg)

    return redirect('self_enrollment_tool:index')
