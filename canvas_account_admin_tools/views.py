import json
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
from proxy.views import proxy_view

from lti_permissions.decorators import (
    lti_permission_required,
    lti_permission_required_check)

logger = logging.getLogger(__name__)
PERMISSIONS = settings.TOOL_PERMISSIONS


@require_http_methods(['GET'])
def tool_config(request):
    url = "%s://%s%s" % (request.scheme, request.get_host(),
                         reverse('lti_launch', exclude_resource_link_id=True))
    title = 'Admin Console'
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
@lti_permission_required(PERMISSIONS['canvas_account_admin_tools'])
@require_http_methods(['GET'])
def dashboard_account(request):
    tools = ['conclude_courses',
             'course_info',
             'cross_list_courses',
             'people_tool']

    # Verify current user permissions to see the apps on the dashboard
    allowed = {tool: lti_permission_required_check(request, PERMISSIONS[tool])
               for tool in tools}
    no_tools_allowed = not any(allowed.values())

    return render(request, 'canvas_account_admin_tools/dashboard_account.html', {
        'allowed': allowed,
        'conclude_courses_url': settings.CONCLUDE_COURSES_URL,
        'no_tools_allowed': no_tools_allowed})


@login_required
@lti_permission_required(PERMISSIONS['canvas_account_admin_tools'])
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

    # tlt-1314: include audit information when creating xlistmaps
    if request.method == 'POST' and 'xlist_maps' in path:
        body_json = json.loads(request.body)
        body_json['last_modified_by'] = request.LTI['lis_person_sourcedid']
        request_args['data'] = json.dumps(body_json)

    url = "{}/{}".format(settings.ICOMMONS_REST_API_HOST, os.path.join(path, ''))
    if settings.ICOMMONS_REST_API_SKIP_CERT_VERIFICATION:
        request_args['verify'] = False
    return proxy_view(request, url, request_args)
