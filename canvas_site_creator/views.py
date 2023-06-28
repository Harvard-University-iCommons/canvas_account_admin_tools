import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from canvas_api.helpers import accounts as canvas_api_accounts
from coursemanager.models import School
from lti_school_permissions.decorators import lti_permission_required
from .utils import create_canvas_course_and_section

from common.utils import get_canvas_site_templates_for_school, get_term_data_for_school

logger = logging.getLogger(__name__)


def lti_auth_error(request):
    raise PermissionDenied


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET', 'POST'])
def create_new_course(request):
    school = None
    sis_account_id = request.LTI['custom_canvas_account_sis_id']

    try:
        school_id = sis_account_id.split(':')[1]
        school = School.objects.get(school_id=school_id)
    except School.objects.DoesNotExist as e:
        logger.exception(f"School does not exist for given sis_account_id: {sis_account_id}")
    if not school:
        return render(request, 'canvas_site_creator/restricted_access.html', status=403)

    canvas_site_templates = get_canvas_site_templates_for_school(school_id)
    terms, _current_term_id = get_term_data_for_school(sis_account_id)

    if request.method == 'POST':
        create_canvas_course_and_section(request)

    context = {'school_id': school_id,
               'school_name': school.title_short,
               'canvas_site_templates': canvas_site_templates,
               'terms': terms}

    return render(request, 'canvas_site_creator/index.html', context)
