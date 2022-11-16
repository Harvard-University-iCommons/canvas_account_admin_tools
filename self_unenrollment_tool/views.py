
import json
import os
from logging import getLogger
from pprint import pformat

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from pylti1p3.contrib.django import (DjangoCacheDataStorage, DjangoDbToolConf,
                                     DjangoMessageLaunch, DjangoOIDCLogin)

from self_enrollment_tool.models import SelfEnrollmentCourse
from icommons_common.models import (CourseEnrollee, CourseGuest,
                                    CourseInstance, CourseStaff, SimplePerson,
                                    UserRole)

logger = getLogger(__name__)


class CustomDjangoMessageLaunch(DjangoMessageLaunch):
    # Override the default validate_deployment() method from DjangoMessageLaunch since we don't want
    # to have to reconfigure the tool every time someone deploys it in a new course or sub-account.
    def validate_deployment(self):
        return self


def get_tool_conf():
    tool_conf = DjangoDbToolConf()
    return tool_conf


def get_launch_data_storage():
    return DjangoCacheDataStorage()


def get_launch_url(request):
    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri


@csrf_exempt
def login(request):
    logger.debug('login')
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()


    oidc_login = DjangoOIDCLogin(request, tool_conf, launch_data_storage=launch_data_storage)
    target_link_uri = get_launch_url(request)
    logger.debug(f'Target link URI: {target_link_uri}')
    return oidc_login.enable_check_cookies().redirect(target_link_uri)


@require_POST
@csrf_exempt
def launch(request):
    logger.debug('Launch request')
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = CustomDjangoMessageLaunch(request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    return redirect(reverse('self_unenrollment_tool:index', kwargs={'launch_id': message_launch.get_launch_id()}))


def index(request, launch_id):
    logger.debug('Self-unenroll index request')
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = CustomDjangoMessageLaunch.from_cache(launch_id, request, tool_conf,
                                                          launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()

    launch_context = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/context')

    deployment_id = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/deployment_id')

    tool_platform = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/tool_platform')

    roles = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/roles')

    lis = message_launch_data.get('https://purl.imsglobal.org/spec/lti/claim/lis')

    course_sis_id = lis.get('course_offering_sourcedid')

    template_context = {}

    # make sure this is a self-enroll course
    se_roles = []
    self_enrollments = []
    is_self_enroll_course = False
    is_self_enrolled = False

    if course_sis_id:
        se_configs = SelfEnrollmentCourse.objects.filter(course_instance_id=course_sis_id)
        for c in se_configs:
            se_roles.append(c.role_id)
            is_self_enroll_course = True

        if is_self_enroll_course:

            user_sis_id = lis.get('person_sourcedid')
            if user_sis_id:
                staff_enrollments = CourseStaff.objects.filter(course_instance_id=course_sis_id, user_id=user_sis_id, source='selfenroll').all()
                student_enrollments = CourseEnrollee.objects.filter(course_instance_id=course_sis_id, user_id=user_sis_id, source='selfenroll').all()
                guest_enrollments = CourseGuest.objects.filter(course_instance_id=course_sis_id, user_id=user_sis_id, source='selfenroll').all()

                for e in staff_enrollments + student_enrollments + guest_enrollments:
                    self_enrollments.append(e)
                    is_self_enrolled = True

    template_context['is_self_enroll_course'] = is_self_enroll_course
    template_context['is_self_enrolled'] = is_self_enrolled
    template_context['self_enrollments'] = self_enrollments
    template_context['self_enrollment_count'] = len(self_enrollments)


    return render(request, 'self_unenrollment_tool/index.html', template_context)


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


LTI_AGS_LINE_ITEM_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
LTI_AGS_LINE_ITEM_READ_ONLY_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
LTI_AGS_RESULT_READ_ONLY_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
LTI_AGS_SCORE_SCOPE = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
LTI_AGS_SHOW_PROGRESS_SCOPE = "https://canvas.instructure.com/lti-ags/progress/scope/show"
LTI_NRPS_V2_SCOPE = "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
LTI_UPDATE_PUBLIC_JWK_SCOPE = "https://canvas.instructure.com/lti/public_jwk/scope/update"
LTI_ACCOUNT_LOOKUP_SCOPE = "https://canvas.instructure.com/lti/account_lookup/scope/show"

def config(request):
    oidc_initiation_url = request.build_absolute_uri(reverse('self_unenrollment_tool:login'))
    target_link_uri = request.build_absolute_uri(reverse('self_unenrollment_tool:launch'))

    # TODO: don't use tool_conf to get the JWKs since it might not exist yet; generate the JWK on the fly from a key in the db

    lms_config = {
        'title': 'Self-unenrollment Tool',
        'description': 'A tool to help users leave courses that they have self-enrolled in',
        'oidc_initiation_url': oidc_initiation_url,
        'target_link_uri': target_link_uri,
        'scopes': [],
        'extensions': [
            {
                'platform': 'canvas.instructure.com',
                'privacy_level': 'public',
                'settings': {
                    'text': 'Self-unenrollment Tool',
                    'icon_url': 'https://www.ltiadvantage.com/wp-content/uploads/2019/01/lti-advantage-logo-white.png',
                    'placements': [
                        {
                            'placement': 'course_home_sub_navigation',
                        },
                    ],
                },
            }
        ],
        'public_jwk': get_tool_conf().get_jwks()['keys'][0],
        'custom_fields': {
            'canvas_user_sisintegrationid': '$Canvas.user.sisIntegrationId',
            'canvas_course_sectionids': '$Canvas.course.sectionIds',
            'canvas_group_contextids': '$Canvas.group.contextIds',
            'canvas_xapi_url': '$Canvas.xapi.url',
            'caliper_url': '$Caliper.url',
        },
    }
    return JsonResponse(lms_config, safe=False)
