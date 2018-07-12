import logging
import json
import time

from django.conf import settings

from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import HttpResponse


from icommons_common.models import School, Term, Department, CourseGroup, Person
from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts

from lti_permissions.decorators import lti_permission_required
from lti_permissions.verification import get_school_sub_account_from_account_id




logger = logging.getLogger(__name__)

COURSE_INSTANCE_FILTERS = ['school', 'term', 'department', 'course_group']


def lti_auth_error(request):
    raise PermissionDenied


@login_required
# @lti_permission_required(settings.PERMISSION_BULK_COURSE_SETTING)
@require_http_methods(['GET'])
def index(request):
    account_sis_id = request.LTI['custom_canvas_account_sis_id']
    context = {'school': account_sis_id[len('school:'):]}
    return render(request, 'bulk_course_settings/index.html', context)
