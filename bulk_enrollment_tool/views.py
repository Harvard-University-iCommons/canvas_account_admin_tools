import logging
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr, Key
from dateutil import tz
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
    if request.method == "POST":
        # TODO: Update/Add logic.
        # logger.info(f'Bulk enrollment file uploaded. File name: '
        #             f'{request.POST.get("bulkEnrollmentFile")}',
        #             extra=request.POST)

        # create_dynamodb_record()
        # store_file_in_s3()

        messages.success(request, f'File uploaded and is being processed.'
                         f'You will get a notification email once complete.')

    # Read data from DynamoDB table.
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(
        settings.BULK_ENROLLMENT_TOOL_SETTINGS['bulk_enrollment_dynamodb_table'])
    response = table.query(
        KeyConditionExpression=Key('pk').eq('SCHOOL#ACTS'),
        Limit=10,
    )
    items = response['Items']

    # Update timestamp to local datetime.
    [item.update(created_at=_convert_time_to_local_datetime(
        item['created_at'])) for item in items]

    context = {
        'most_recently_uploaded_files': items
    }
    return render(request, 'bulk_enrollment_tool/index.html', context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def download(request, s3_key, filename):
    # generate an S3 URL and redirect to it.
    logger.debug(f'generating an S3 url for {s3_key}')
    bucket_name = settings.BULK_ENROLLMENT_TOOL_SETTINGS['bulk_enrollment_s3_bucket']

    s3 = boto3.client('s3')
    s3_url = s3.generate_presigned_url(
        'get_object',
        {
            'Bucket': bucket_name,
            'Key': s3_key,
            'ResponseContentDisposition': f'attachment;filename={filename}',
        },
        ExpiresIn=60
    )
    logger.debug(s3_url)
    return redirect(s3_url)


def create_dynamodb_record() -> None:
    """
    Creates bulk enrollment record in DynamoDB table.
    """
    # TODO: Update/Add logic.
    # logger.debug('Create bulk enrollment DynamoDB record', extra={})

    # See docs here on how to use Boto3 to read, create records, etc... in DynamoDB:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html

    # Docs for DynamoDB request syntax :https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Query.html
    return None


def store_file_in_s3() -> None:
    """
    Stores user bulk enrollment uploaded file in S3 bucket.
    """
    # TODO: Update/Add logic.
    # logger.debug('Store bulk enrollment file in S3', extra={})

    # See docs here on how to use Boto3 to read, create records, etc... in DynamoDB:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html

    # Docs for DynamoDB request syntax :https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_Query.html
    return None


def _convert_time_to_local_datetime(date_time: str) -> datetime:
    # Auto-detect zones:
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    # utc = datetime.utcnow()
    utc = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S.%f')

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default.
    utc = utc.replace(tzinfo=from_zone)

    # Return converted time zone.
    return utc.astimezone(to_zone)
