import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@require_http_methods(['GET'])
def index(request):
    return render(request, 'course_info/index.html', {})
