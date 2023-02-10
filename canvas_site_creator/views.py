import json
import logging
import time

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts
from icommons_common.models import School
from lti_permissions.decorators import lti_permission_required

from common.utils import (
    get_canvas_site_templates_for_school,
)

logger = logging.getLogger(__name__)

COURSE_INSTANCE_FILTERS = ['school', 'term', 'department', 'course_group']


def lti_auth_error(request):
    raise PermissionDenied

@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET'])
def create_new_course(request):
    start_time = time.time()
    canvas_user_id = request.LTI['custom_canvas_user_id']
    sis_account_id = request.LTI['custom_canvas_account_sis_id']

    # Fetch school data from DB
    try:
        school_id = sis_account_id.split(':')[1]
        school = School.objects.get(school_id=school_id)
    except:
        logger.exception("Error retrieving school information for sis_account_id=%s" % sis_account_id)
        return HttpResponse(json.dumps({'error': 'retrieving school information for sis_account_id=%s' % sis_account_id}),
                            content_type="application/json", status=500)
    if not school:
        return render(request, 'canvas_site_creator/restricted_access.html',
                      status=403)

    canvas_site_templates = get_canvas_site_templates_for_school(school_id)

    logger.debug("\n\n--------->Initial load of the create_new_course view took : %s seconds" % (time.time() - start_time))
    return render(request, 'canvas_site_creator/create_new_course.html',
                  {'school_id': school_id, 'school_name': school.title_short,
                   'canvas_site_templates': canvas_site_templates})

