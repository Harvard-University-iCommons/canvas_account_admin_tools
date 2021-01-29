import logging
import boto3
import json

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
@lti_permission_required(settings.PERMISSION_MASQUERADE_TOOL)
@require_http_methods(['GET'])
def index(request):
    context = {}
    return render(request, 'masquerade_tool/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_MASQUERADE_TOOL)
@require_http_methods(['GET', 'POST'])
def add_role(request):
    canvas_user_id = request.LTI['custom_canvas_user_id']
    lambda_client = boto3.client('lambda')

    payload = {
        'user_id': canvas_user_id,
        'action': 'add',
    }
    result = lambda_client.invoke(
        FunctionName='arn:aws:lambda:us-east-1:482956169056:function:temporary-masquerade-dev-TemporaryMasqueradeFuncti-1IECMNSLQXP1X',
        Payload=json.dumps(payload),
    )
    print(result)
    return render(request, 'masquerade_tool/index.html')
