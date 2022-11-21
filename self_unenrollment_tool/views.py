
from logging import getLogger

from canvas_sdk import RequestContext
from canvas_sdk.methods.enrollments import (conclude_enrollment,
                                            list_enrollments_courses)
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from icommons_common.models import CourseEnrollee, CourseGuest, CourseStaff
from pylti1p3.contrib.django import (DjangoCacheDataStorage, DjangoDbToolConf,
                                     DjangoMessageLaunch, DjangoOIDCLogin)

from self_enrollment_tool.models import SelfEnrollmentCourse

from .lti1p3_utils import get_message_launch, require_lti_launch, get_launch_url

logger = getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)


@csrf_exempt
def login(request: HttpRequest):
    tool_conf = DjangoDbToolConf()
    launch_data_storage = DjangoCacheDataStorage()

    oidc_login = DjangoOIDCLogin(request, tool_conf, launch_data_storage=launch_data_storage)
    target_link_uri = get_launch_url(request)
    return oidc_login.enable_check_cookies().redirect(target_link_uri)


@require_POST
@csrf_exempt
def launch(request: HttpRequest):
    message_launch = get_message_launch(request)
    # this next line is necessary even if the variable is not used; if get_launch_data() is not called, launch data will not be saved to the session!
    launch_data = message_launch.get_launch_data()
    logger.info('self_unenrollment_tool launch', extra={'launch_data': launch_data})
    return redirect(reverse('self_unenrollment_tool:index', kwargs={'launch_id': message_launch.get_launch_id()}))


@require_lti_launch
def index(request: HttpRequest, launch_id):
    try:
        message_launch = get_message_launch(request, launch_id)
        launch_data = message_launch.get_launch_data()
        lis = launch_data['https://purl.imsglobal.org/spec/lti/claim/lis']
        course_sis_id = lis['course_offering_sourcedid']
        user_sis_id = lis['person_sourcedid']
        extra = {
            'course_sis_id': course_sis_id,
            'user_sis_id': user_sis_id,
            'launch_data': launch_data,
        }
    except Exception as e:
        logger.exception(f'Failed to launch self-unenroll tool: {e}', extra=extra)
        return render(request, 'self_unenrollment_tool/error.html', {'message': 'There was a problem launching the tool.'})


    if request.method == 'GET':

        template_context = {}

        # make sure this is a self-enroll course
        self_enrollments = []
        is_self_enroll_course = False
        is_self_enrolled = False

        if course_sis_id:
            se_configs = SelfEnrollmentCourse.objects.filter(course_instance_id=course_sis_id)
            for c in se_configs:
                logger.debug(f'Self-enrollment is active for role {c.role_id} (link UUID: {c.uuid})')
                is_self_enroll_course = True

            if is_self_enroll_course:
                if user_sis_id:
                    self_enrollments = _get_self_enrollments(course_sis_id=course_sis_id, user_sis_id=user_sis_id)
                    if self_enrollments:
                        is_self_enrolled = True
                        for se in self_enrollments:
                            logger.debug(se)

        template_context['is_self_enroll_course'] = is_self_enroll_course
        template_context['is_self_enrolled'] = is_self_enrolled
        template_context['self_enrollments'] = self_enrollments
        template_context['self_enrollment_count'] = len(self_enrollments)

        return render(request, 'self_unenrollment_tool/index.html', template_context)

    elif request.method == 'POST':

        # first, get all of the user's Canvas enrollments
        api_response = list_enrollments_courses(request_ctx=SDK_CONTEXT, course_id=f'sis_course_id:{course_sis_id}', user_id=f'sis_user_id:{user_sis_id}')
        if api_response.status_code == 200:
            canvas_enrollments = api_response.json()
            for ce in canvas_enrollments:
                logger.debug(ce)
        else:
            logger.error(f'bad response from Canvas API: {api_response.text}', extra=extra)

        # get the user's self-enrollments from our database
        self_enrollments = _get_self_enrollments(course_sis_id=course_sis_id, user_sis_id=user_sis_id)

        for se in self_enrollments:
            logger.debug(se)
            se_user_id = se.user_id
            se_course_instance_id = se.course_instance_id
            se_role_id = se.role_id
            extra['se_role_id'] = se_role_id
            canvas_role_id = se.role.canvas_role_id
            se.delete()
            logger.info(f'deleted self enrollment for user {se_user_id}, course_instance {se_course_instance_id}, role {se_role_id}', extra=extra)

            for ce in canvas_enrollments:
                if ce['role_id'] == canvas_role_id:
                    # we need to delete this one
                    conclude_enrollment(request_ctx=SDK_CONTEXT, course_id=ce['course_id'], id=ce['id'], task='delete')
                    logger.info(f'deleted Canvas enrollment id {ce["id"]} in course {ce["course_id"]}', extra=extra)

        return redirect(reverse('self_unenrollment_tool:success', kwargs={'launch_id': launch_id}))


def _get_self_enrollments(course_sis_id, user_sis_id):
    # this function fetches all three types of enrollment and returns them in one list
    enrollments = []
    staff_enrollments = CourseStaff.objects.filter(course_instance_id=course_sis_id, user_id=user_sis_id, source='selfenroll').all()
    student_enrollments = CourseEnrollee.objects.filter(course_instance_id=course_sis_id, user_id=user_sis_id, source='selfenroll').all()
    guest_enrollments = CourseGuest.objects.filter(course_instance_id=course_sis_id, user_id=user_sis_id, source='selfenroll').all()
    for e in staff_enrollments:
        enrollments.append(e)
    for e in student_enrollments:
        enrollments.append(e)
    for e in guest_enrollments:
        enrollments.append(e)
    return enrollments


def error(request: HttpRequest, message=None):
    template_context = {
        'message': message
    }
    return render(request, 'self_unenrollment_tool/error.html', template_context)


def success(request: HttpRequest, launch_id):
    template_context = {}
    return render(request, 'self_unenrollment_tool/success.html', template_context)


def get_jwks(request: HttpRequest):
    tool_conf = DjangoDbToolConf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


LTI_AGS_LINE_ITEM_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
LTI_AGS_LINE_ITEM_READ_ONLY_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
LTI_AGS_RESULT_READ_ONLY_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
LTI_AGS_SCORE_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
LTI_AGS_SHOW_PROGRESS_SCOPE = "https://canvas.instructure.com/lti-ags/progress/scope/show"
LTI_NRPS_V2_SCOPE = "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
LTI_UPDATE_PUBLIC_JWK_SCOPE = "https://canvas.instructure.com/lti/public_jwk/scope/update"
LTI_ACCOUNT_LOOKUP_SCOPE = "https://canvas.instructure.com/lti/account_lookup/scope/show"

def config(request: HttpRequest):
    oidc_initiation_url = request.build_absolute_uri(reverse('self_unenrollment_tool:login'))
    target_link_uri = request.build_absolute_uri(reverse('self_unenrollment_tool:launch'))
    # if the tool needs LTI Advantage scopes, add them here:
    scopes = []
    # get the JWK (we're just using the first key we find)
    # todo: generate a new key if one doesn't exist yet?
    public_jwk = DjangoDbToolConf().get_jwks()['keys'][0]
    # if the tool needs custom Canvas fields, add them here:
    custom_fields = {
        'canvas_user_sisintegrationid': '$Canvas.user.sisIntegrationId',
        'canvas_course_id': '$Canvas.course.id',
        'canvas_course_sectionids': '$Canvas.course.sectionIds',
        'canvas_course_section_sis_sourceids': '$Canvas.course.sectionSisSourceIds',
        'canvas_xapi_url': '$Canvas.xapi.url',
        'caliper_url': '$Caliper.url',
    }

    lms_config = {
        'title': 'Self-unenrollment Tool',
        'description': 'A tool to help users leave courses that they have self-enrolled in',
        'oidc_initiation_url': oidc_initiation_url,
        'target_link_uri': target_link_uri,
        'scopes': scopes,
        'extensions': [
            {
                'platform': 'canvas.instructure.com',
                'privacy_level': 'public',
                'settings': {
                    'text': 'Self-unenrollment Tool',
                    'placements': [
                        {
                            'placement': 'course_home_sub_navigation',
                            'text': 'Un-enroll from this course'
                        },
                    ],
                },
            }
        ],
        'public_jwk': public_jwk,
        'custom_fields': custom_fields,
    }
    return JsonResponse(lms_config, safe=False)
