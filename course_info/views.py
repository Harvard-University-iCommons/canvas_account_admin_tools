import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required

from course_info.canvas import get_administered_school_accounts


logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@require_http_methods(['GET'])
def index(request):
    canvas_user_id = request.LTI['custom_canvas_user_id']
    accounts = get_administered_school_accounts(canvas_user_id)
    schools = [(a['sis_account_id'].split(':')[1], a['name']) for a in accounts]
    schools.sort(key=lambda r: r[1])
    context = {
        'schools': schools,
    }
    return render(request, 'course_info/index.html', context)
