import logging
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ims_lti_py.tool_config import ToolConfig

from canvas_account_admin_tools.models import ExternalTool

from proxy.views import proxy_view
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def tool_config(request):
    url = "%s://%s%s" % (request.scheme, request.get_host(),
                         reverse('lti_launch', exclude_resource_link_id=True))
    title = 'Account Admin Tasks'
    lti_tool_config = ToolConfig(
        title=title,
        launch_url=url,
        secure_launch_url=url,
        description="This LTI tool provides a suite of tools for administering your Canvas account."
    )

    # this is how to tell Canvas that this tool provides an account navigation link:
    nav_params = {
        'enabled': 'true',
        'text': title,
        'default': 'disabled',
        'visibility': 'admins',
    }
    custom_fields = {'canvas_membership_roles': '$Canvas.membership.roles'}
    lti_tool_config.set_ext_param('canvas.instructure.com', 'custom_fields', custom_fields)
    lti_tool_config.set_ext_param('canvas.instructure.com', 'account_navigation', nav_params)
    lti_tool_config.set_ext_param('canvas.instructure.com', 'privacy_level', 'public')

    return HttpResponse(lti_tool_config.to_xml(), content_type='text/xml')


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def lti_launch(request):
    return redirect('dashboard_account')


@login_required
@lti_role_required(const.ADMINISTRATOR)
@require_http_methods(['GET'])
def dashboard_account(request):
    custom_canvas_account_id = request.LTI['custom_canvas_account_id']

    canvas_site_creator = ExternalTool.objects.get_external_tool_url_by_name_and_canvas_account_id(
        ExternalTool.CANVAS_SITE_CREATOR,
        custom_canvas_account_id
    )

    manage_courses = [
        canvas_site_creator,
    ]

    conclude_courses = settings.CONCLUDE_COURSES_URL
    lti_tools_usage = ExternalTool.objects.get_external_tool_url_by_name_and_canvas_account_id(
        ExternalTool.LTI_TOOLS_USAGE,
        custom_canvas_account_id
    )
    courses_in_this_account = ExternalTool.objects.get_external_tool_url_by_name_and_canvas_account_id(
        ExternalTool.COURSES_IN_THIS_ACCOUNT,
        custom_canvas_account_id
    )

    # todo: confirm what conditions need to be met for course_info to be available
    course_info = True
    manage_account = [
        conclude_courses,
        lti_tools_usage,
        courses_in_this_account,
        course_info
    ]

    return render(request, 'canvas_account_admin_tools/dashboard_account.html', {
        'has_manage_courses': any(manage_courses),
        'has_manage_account': any(manage_account),
        'canvas_site_creator': canvas_site_creator,
        'conclude_courses': conclude_courses,
        'lti_tools_usage': lti_tools_usage,
        'courses_in_this_account': courses_in_this_account,
        'course_info': course_info
    })


@login_required
def icommons_rest_api_proxy(request, path):
    request_args = {
        'headers': {
            'Authorization': "Token {}".format(settings.ICOMMONS_REST_API_TOKEN)
        }
    }

    # Remove resource_link_id query param
    # request.GET is immutable, so we need to copy before modifying
    request.GET = request.GET.copy()
    request.GET.pop('resource_link_id', None)

    url = "{}/{}".format(settings.ICOMMONS_REST_API_HOST, os.path.join(path, ''))
    if settings.ICOMMONS_REST_API_SKIP_CERT_VERIFICATION:
        request_args['verify'] = False
    return proxy_view(request, url, request_args)
