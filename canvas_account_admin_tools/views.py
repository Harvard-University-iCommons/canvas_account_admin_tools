import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti import ToolConfig
from lti_permissions.decorators import lti_permission_required
from lti_permissions.verification import is_allowed
from proxy.views import proxy_view

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def tool_config(request):
    logger.debug("called tool_config()")
    url = "https://{}{}".format(request.get_host(), reverse('lti_launch'))
    url = _url(url)

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


def _url(url):
    """
    *** Taken from ATG's django-app-lti repo to fix the issue of resource_link_id being included in the launch url
    *** TLT-3591
    Returns the URL with the resource_link_id parameter removed from the URL, which
    may have been automatically added by the reverse() method. The reverse() method is
    patched by django-auth-lti in applications using the MultiLTI middleware. Since
    some applications may not be using the patched version of reverse(), we must parse the
    URL manually and remove the resource_link_id parameter if present. This will
    prevent any issues upon redirect from the launch.
    """

    parts = urllib.parse.urlparse(url)
    query_dict = urllib.parse.parse_qs(parts.query)
    if 'resource_link_id' in query_dict:
        query_dict.pop('resource_link_id', None)
    new_parts = list(parts)
    new_parts[4] = urllib.parse.urlencode(query_dict)
    return urllib.parse.urlunparse(new_parts)


@login_required
@require_http_methods(['POST'])
@csrf_exempt
def lti_launch(request):
    return redirect('dashboard_account')


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_ACCOUNT_ADMIN_TOOLS)
@require_http_methods(['GET'])
def dashboard_account(request):
    logger.info(request.LTI)
    custom_canvas_account_sis_id = request.LTI['custom_canvas_account_sis_id']
    custom_canvas_membership_roles = request.LTI['custom_canvas_membership_roles']
    build_info = settings.BUILD_INFO

    """
    Verify that the current user has permission to see the Search Courses (aka course_info) tool
    """
    search_courses_allowed = is_allowed(
        custom_canvas_membership_roles,
        settings.PERMISSION_SEARCH_COURSES,
        canvas_account_sis_id=custom_canvas_account_sis_id
    )

    """
    Verify that the current user has permission to see the cross listing button
    on the dashboard TLT-2569
    """
    cross_listing_is_allowed = is_allowed(custom_canvas_membership_roles,
                                          settings.PERMISSION_XLIST_TOOL,
                                          canvas_account_sis_id=custom_canvas_account_sis_id)

    """
    verify that user has permissions to view the People tool
    """
    people_tool_is_allowed = is_allowed(custom_canvas_membership_roles,
                                        settings.PERMISSION_PEOPLE_TOOL,
                                        canvas_account_sis_id=custom_canvas_account_sis_id)

    """
    verify that user has permissions to view the canvas site creator tool
    """
    site_creator_is_allowed = is_allowed(custom_canvas_membership_roles,
                                         settings.PERMISSION_SITE_CREATOR,
                                         canvas_account_sis_id=custom_canvas_account_sis_id)

    """
    verify that user has permissions to view the publish courses tool
    """
    publish_courses_allowed = is_allowed(custom_canvas_membership_roles,
                                         settings.PERMISSION_PUBLISH_COURSES,
                                         canvas_account_sis_id=custom_canvas_account_sis_id)

    """
    verify that user has permissions to view the bulk course settings tool
    """
    bulk_course_settings_is_allowed = is_allowed(custom_canvas_membership_roles,
                                                 settings.PERMISSION_BULK_COURSE_SETTING,
                                                 canvas_account_sis_id=custom_canvas_account_sis_id)

    """
       verify that user has permissions to view the Canvas Site deletion tool
       """
    canvas_site_deletion_is_allowed = is_allowed(custom_canvas_membership_roles,
                                                 settings.PERMISSION_CANVAS_SITE_DELETION,
                                                 canvas_account_sis_id=custom_canvas_account_sis_id)
    """
        verify that user has permissions to view the masquerade tool
        """
    masquerade_tool_is_allowed = is_allowed(custom_canvas_membership_roles,
                                            settings.PERMISSION_MASQUERADE_TOOL,
                                            canvas_account_sis_id=custom_canvas_account_sis_id)

    return render(request, 'canvas_account_admin_tools/dashboard_account.html', {
        'search_courses_allowed': search_courses_allowed,
        'cross_listing_allowed': cross_listing_is_allowed,
        'people_tool_allowed': people_tool_is_allowed,
        'site_creator_is_allowed': site_creator_is_allowed,
        'publish_courses_allowed': publish_courses_allowed,
        'bulk_course_settings_is_allowed': bulk_course_settings_is_allowed,
        'canvas_site_deletion_is_allowed': canvas_site_deletion_is_allowed,
        'masquerade_tool_is_allowed': masquerade_tool_is_allowed,
        'build_info': build_info
    })


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_ACCOUNT_ADMIN_TOOLS)
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

    response = proxy_view(request, url, request_args)
    try:
        params = request.GET
        if request.method == 'PATCH':
            params = json.loads(request.body)
        elif request.method == 'POST':
            params = json.loads(request.body)

        extra = {
            'user': request.user.username,
            'path': request.path,
            'method': request.method,
            'query_string': request.META.get('QUERY_STRING'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'remote_addr': request.META.get('REMOTE_ADDR'),
            'referrer': request.META.get('HTTP_REFERER'),
            'status_code': response.status_code,
            'params': params,
        }

        logger.info(f'User {request.user.username} requesting {request.method} {url}', extra=extra)
    except Exception:
        logger.error(f'Error logging request by {request.user.username} to {url}')

    return response
