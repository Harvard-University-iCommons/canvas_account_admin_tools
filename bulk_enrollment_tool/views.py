import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET', 'POST'])
def index(request):
    context = {
        'message': 'Hello!!!'
    }
    return render(request, 'bulk_enrollment_tool/index.html', context=context)


def create_dynamodb_record() -> None:
    """
    Creates bulk enrollment record in DynamoDB table.
    """
    return None


def store_file_in_s3() -> None:
    """
    Stores user bulk enrollment uploaded file in S3 bucket.
    """
    return None
