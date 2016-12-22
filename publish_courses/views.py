# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def index(request):
    account_sis_id = request.LTI['custom_canvas_account_sis_id']
    context = {'school': account_sis_id.lstrip('school:')}
    return render(request, 'publish_courses/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'publish_courses/partials/' + path, {})
