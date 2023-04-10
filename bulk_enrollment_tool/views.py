import logging
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Attr, Key
from dateutil import tz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required
from ulid import ULID

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET', 'POST'])
def index(request):
    if request.method == "POST":
        logger.info(f'Bulk enrollment file uploaded. File: '
                    f'{request.FILES["bulkEnrollmentFile"]}')

        _create_dynamodb_record(request)

        messages.success(request, f'File uploaded and is being processed. '
                         f'You will get a notification email once complete.')

        return redirect('bulk_enrollment_tool:index')

    tool_launch_school = get_tool_launch_school(request)

    # Read data from DynamoDB table (get n most recent records).
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(
        settings.BULK_ENROLLMENT_TOOL_SETTINGS['bulk_enrollment_dynamodb_table'])
    response = table.query(
        KeyConditionExpression=Key('pk').eq(f'SCHOOL#{tool_launch_school.upper()}'),
        ScanIndexForward=False,  # Records in reverse order (DESC).
        Limit=10,
    )
    items = response['Items']

    # Update timestamp to local datetime.
    [item.update(created_at=convert_time_to_local_datetime(
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


def _create_dynamodb_record(request) -> None:
    """
    Creates bulk enrollment record in DynamoDB table.
    """
    be_table_name = settings.BULK_ENROLLMENT_TOOL_SETTINGS['bulk_enrollment_dynamodb_table']

    filename = request.FILES['bulkEnrollmentFile'].name
    school_id = get_tool_launch_school(request)
    uploaded_by = request.LTI['lis_person_name_full']

    ddb_resource = boto3.resource('dynamodb')
    be_table = ddb_resource.Table(be_table_name)

    # generate a ulid for the file id
    file_id = str(ULID())
    s3_key = f'{school_id}/{file_id}.csv'

    logger.debug(f'Create bulk enrollment DynamoDB record. File ID: {file_id}')

    # put a record in the dynamodb table
    pk = f'SCHOOL#{school_id.upper()}'
    sk = f'FILE#{file_id}'

    be_table.put_item(
        Item={
            'pk': pk,
            'sk': sk,
            'status': 'new',
            'created_at': str(datetime.utcnow()),
            'updated_at': str(datetime.utcnow()),
            # the front-end tool will likely want to store additional attributes here, such as:
            'original_filename': filename,
            's3_key': s3_key,
            'uploaded_by': uploaded_by,
        }
    )

    _store_file_in_s3(request, s3_key)

    return None


def _store_file_in_s3(request, filename: str) -> None:
    """
    Stores user bulk enrollment uploaded file in S3 bucket.
    """
    be_s3_bucket_name = settings.BULK_ENROLLMENT_TOOL_SETTINGS['bulk_enrollment_s3_bucket']

    # Stream content into S3 bucket.
    s3 = boto3.resource('s3')
    response = s3.Object(be_s3_bucket_name, filename).put(
        Body=request.FILES['bulkEnrollmentFile'].file.getvalue())

    logger.debug(
        f'Store bulk enrollment file in S3. File ID: {filename}', extra=response)

    return None


def convert_time_to_local_datetime(date_time: str) -> datetime:
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


def get_tool_launch_school(request) -> str:
    """
    Get the school that this tool is being launched in.
    """
    try:
        tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]
    except Exception:
        logger.exception('Error getting launch school')

    return tool_launch_school
