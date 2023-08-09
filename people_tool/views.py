import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from lti_school_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_permission_required(settings.PERMISSION_PEOPLE_TOOL)
@require_http_methods(['GET'])
def index(request):
    return render(request, 'people_tool/index.html')


@login_required
@lti_permission_required(settings.PERMISSION_PEOPLE_TOOL)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'people_tool/partials/' + path, {})
