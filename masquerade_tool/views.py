import logging
import boto3
import json
import dateutil.parser

from icommons_common.canvas_utils import SessionInactivityExpirationRC

from datetime import datetime
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
        logger.info('User {} requested masquerade access at {}'.format(
            request.LTI['lis_person_name_full'], datetime.now()))

        # TODO: move the region_name to SSM
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        payload = {
            'user_id': canvas_user_id,
            'action': 'add',
        }
        logger.debug('payload :{}'.format(payload))
        # TODO: move move the FunctionName to SSM
        result = lambda_client.invoke(
            FunctionName='arn:aws:lambda:us-east-1:482956169056:function:temporary-masquerade-dev-TemporaryMasqueradeFuncti-1IECMNSLQXP1X',
            Payload=json.dumps(payload),
        )
        logger.info('lambda result = {}'.format(result))
        invoke_status = result['ResponseMetadata']['HTTPStatusCode']
        response_payload = json.loads(result['Payload'].read().decode("utf-8"))

        status = response_payload["status"]
        exp_dt = None
        # Check if expires is being sent. if role already exists, expires won't be set.
        if "expires" in response_payload:
            exp_dt = dateutil.parser.isoparse(response_payload["expires"])

        logger.info(' payload response =  {}'.format( response_payload))
        context = {'expiry_time': exp_dt, 'status': status}
    except Exception as e:
        logger.error(e)

    return render(request, 'masquerade_tool/success.html', context)
