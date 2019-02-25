import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.models import XlistMap
from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def index(request):
    today = datetime.now()
    # The school that this tool is being launched in
    tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]

    # Only get cross listings with current or future terms
    xlist_maps = XlistMap.objects.filter(
                    primary_course_instance__term__end_date__gte=today).filter(
                    secondary_course_instance__term__end_date__gte=today
                ) | XlistMap.objects.filter(primary_course_instance__term__end_date__isnull=True) | \
                    XlistMap.objects.filter(secondary_course_instance__term__end_date__isnull=True)

    context = {
        'xlist_maps': xlist_maps[:10],  # Only getting 10 results to temporarily reduce loading time
        'tool_launch_school': tool_launch_school
    }

    return render(request, 'list.html', context=context)
