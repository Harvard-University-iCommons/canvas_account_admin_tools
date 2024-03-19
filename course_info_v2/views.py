import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_COURSE_INFO_V2)
@require_http_methods(['GET'])
def index(request):
    canvas_user_id = request.LTI['custom_canvas_user_id']

    return render(request, "course_info_v2/course_search.html", context={})

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_COURSE_INFO_V2)
@require_http_methods(['GET'])
def details(request):
    return render(request, "course_info_v2/course_details.html", context={})


