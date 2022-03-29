import logging
import boto3
import json
import dateutil.parser


from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)
AWS_REGION_NAME = settings.MASQUERADE_TOOL_SETTINGS['aws_region_name']
FUNCTION_ARN = settings.MASQUERADE_TOOL_SETTINGS['temporary_masquerade_function_arn']
MASQUERADE_SESSION_MINS = settings.MASQUERADE_TOOL_SETTINGS['masquerade_session_minutes']


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_MASQUERADE_TOOL)
@require_http_methods(['GET'])
def index(request):
    context = {'session_mins': MASQUERADE_SESSION_MINS}
    return render(request, 'masquerade_tool/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_MASQUERADE_TOOL)
@require_http_methods(['POST'])
def add_role(request):
    context = {}
    try:
        canvas_user_id = request.LTI['custom_canvas_user_id']
        logger.info('User {} requested masquerade access at {}'.format(
            request.LTI['lis_person_name_full'], datetime.now()))

        lambda_client = boto3.client('lambda', region_name=AWS_REGION_NAME)
        payload = {
            'user_id': canvas_user_id,
            'action': 'add',
        }
        logger.debug('payload :{}'.format(payload))
        result = lambda_client.invoke(
            FunctionName=FUNCTION_ARN,
            Payload=json.dumps(payload),
        )
        invoke_status = result['ResponseMetadata']['HTTPStatusCode']
        logger_method = logger.info if str(invoke_status) == '200' else logger.error
        logger_method(
            f"lambda FUNCTION_ARN={FUNCTION_ARN} "
            f"status={invoke_status} "
            f"result={result}",
            extra={"invoke_status": invoke_status, "result": result}
        )

        response_payload = json.loads(result['Payload'].read().decode("utf-8"))
        status = response_payload.get("status")

        if status is None or str(status) == 'error':
            raise(ValueError(f'Unexpected status={status}; response_payload={response_payload}'))

        logger.info(' payload response =  {}'.format(response_payload))

        exp_dt = None
        # Check if 'expires' is being sent. If role already exists, expires won't be set.
        if "expires" in response_payload:
            exp_dt = dateutil.parser.isoparse(response_payload["expires"])
        context = {'expiry_time': exp_dt, 'status': status, 'session_mins': MASQUERADE_SESSION_MINS}

    except Exception as e:
        requestor_name = getattr(request, 'LTI', {}).get(
            'lis_person_name_full',
            '(list_person_name_full missing from LTI context)'
        )
        logger.error(f"Error while processing request from {requestor_name}")
        logger.exception(e)
        return render(request, 'masquerade_tool/error.html', context)

    return render(request, 'masquerade_tool/success.html', context)
