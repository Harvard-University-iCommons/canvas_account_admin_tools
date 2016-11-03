import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_permission_required('cross_listing')
@require_http_methods(['GET'])
def index(request):
    return render(request, 'cross_list_courses/index.html')


@login_required
@lti_permission_required('cross_listing')
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'cross_list_courses/partials/' + path, {})
