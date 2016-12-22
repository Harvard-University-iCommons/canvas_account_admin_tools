# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_permissions.decorators import lti_permission_required
from lti_permissions.verification import get_school_sub_account_from_account_id
from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts


logger = logging.getLogger(__name__)

COURSE_INSTANCE_FILTERS = ['school', 'term']

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def index(request):
    account_sis_id = request.LTI['custom_canvas_account_sis_id']
    context = {'school': account_sis_id.lstrip('school:')}
#     # prep context data, used to fill filter dropdowns with data targeted
#     # to the lti launch's user.
#     canvas_user_id = request.LTI['custom_canvas_user_id']
#     sis_account_id = request.LTI['custom_canvas_account_sis_id']
#     school_id = sis_account_id.split(':')[1]
#     ci_filters = {key: request.GET.get(key, '')
#                   for key in COURSE_INSTANCE_FILTERS}
#     schools = json.loads(_get_schools_context(canvas_user_id))
#     print schools
#
#     # fetch the current school data
#     school = [school for school in schools if school['value'] == school_id]
#     print "school=====", school
#     context = {
#         'schools': _get_schools_context(canvas_user_id),
#         'filters': ci_filters,
#         'school': json.dumps(school),
#     }
# >>>>>>> Stashed changes
    return render(request, 'publish_courses/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'publish_courses/partials/' + path, {})
