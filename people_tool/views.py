import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from lti_permissions.decorators import lti_permission_required
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required

logger = logging.getLogger(__name__)


# todo: re-enable lti_permission_required()
@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_PEOPLE_TOOL)
@require_http_methods(['GET'])
def index(request):
    return render(request, 'people_tool/index.html')


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_PEOPLE_TOOL)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'people_tool/partials/' + path, {})
