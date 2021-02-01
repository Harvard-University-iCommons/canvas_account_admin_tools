import logging
import boto3
import json

from datetime import datetime,timedelta
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
    context = {}
    try:
        canvas_user_id = request.LTI['custom_canvas_user_id']
        now = datetime.now()
        expiry_time = datetime.now() + timedelta(hours=1)
        formatted_time = format(expiry_time, '%A %Y-%m-%d %H:%M:%S')
        logger.info('User {} requested masqeurade access at {}, for one hour until {}'.format(
            request.user, now, formatted_time ))

        expiry_time
        lambda_client = boto3.client('lambda')
        payload = {
            'user_id': canvas_user_id,
            'action': 'add',
        }
        result = lambda_client.invoke(
            FunctionName='arn:aws:lambda:us-east-1:482956169056:function:temporary-masquerade-dev-TemporaryMasqueradeFuncti-1IECMNSLQXP1X',
            Payload=json.dumps(payload),
        )
        logger.info(result)
        status = result['ResponseMetadata']['HTTPStatusCode']
        context = {'expiry_time': formatted_time}
    except Exception as e:
        logger.error(e)

    return render(request, 'masquerade_tool/success.html', context)
