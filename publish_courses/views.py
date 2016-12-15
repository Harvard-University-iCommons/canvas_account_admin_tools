import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from lti_permissions.decorators import lti_permission_required
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required

from canvas_account_admin_tools.utils import _get_schools_context

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def index(request):
    # prep context data, used to fill filter dropdowns with data targeted
    # to the lti launch's user.
    canvas_user_id = request.LTI['custom_canvas_user_id']
    context = {
        'schools': _get_schools_context(canvas_user_id),
    }
    return render(request, 'publish_courses/index.html', context)

@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'publish_courses/partials/' + path, {})
