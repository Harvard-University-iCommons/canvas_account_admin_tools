import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from lti_permissions.decorators import lti_permission_required
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.models import XlistMap

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def index(request):

    return render(request, 'cross_list_courses/index.html')


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'cross_list_courses/partials/' + path, {})

