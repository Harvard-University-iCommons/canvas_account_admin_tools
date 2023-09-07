import logging

import boto3
from boto3.dynamodb.conditions import Key
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required
from ulid import ULID

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET', 'POST'])
def index(request):

    if request.method == "POST":
        logger.info(f'Bulk enrollment file uploaded. File: '
                    f'{request.FILES["bulkEnrollmentFile"]}')

        _create_dynamodb_record(request)

        filename = request.FILES['bulkEnrollmentFile'].name
        messages.success(
            request, f'File {filename} has been uploaded and is being processed. It may take up to 5 minutes for changes to be reflected in Canvas.')

        return redirect('bulk_enrollment_tool:index')

    tool_launch_school = get_tool_launch_school(request)

    if not tool_launch_school:
        template_context = {
            'error_title': 'Error',
            'error_message': 'Sorry, this tool can only be used in a school-level sub-account.'
        }
        return render(request, 'canvas_account_admin_tools/error.html', context=template_context)

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

    # Update string timestamp to datetime.
    [item.update(created_at=parse_datetime(item['created_at']))
     for item in items]

    context = {
        'most_recently_uploaded_files': items
    }
    return render(request, 'bulk_enrollment_tool/index.html', context=context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def download(request, s3_key: str, filename: str):
    """
    Generates an S3 URL and redirect to it.
    """
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
    logger.debug(f'S3 URL: {s3_url}')
    return redirect(s3_url)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def errors(request, pk: str, sk: str):
    """
    This function renders the error page for a specified DynamoDB record.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(
        settings.BULK_ENROLLMENT_TOOL_SETTINGS['bulk_enrollment_dynamodb_table'])
    response = table.get_item(
        Key={
            'pk': pk,
            'sk': sk
        }
    )

    # Slice errors string to remove `["` and `"]` at the beginning and end.
    # Then update errors string to be a list of errors.
    response['Item'].update(errors=response['Item']
                            ['errors'][2:-2].split('", "'))
    # Update string timestamp to datetime.
    response['Item'].update(created_at=parse_datetime(
        response['Item']['created_at']))

    return render(request, 'bulk_enrollment_tool/errors_page.html',
                  context={'item': response['Item']})


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_ENROLLMENT_TOOL)
@require_http_methods(['GET'])
def help(request):
    return render(request, 'bulk_enrollment_tool/help.html')


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
            'created_at': str(timezone.now()),  # UTC time-zone-aware datetime.
            'updated_at': str(timezone.now()),
            # Additional attributes:
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


def get_tool_launch_school(request) -> str:
    """
    Get the school that this tool is being launched in.
    """
    try:
        if request.LTI['custom_canvas_account_sis_id'].startswith('school:'):
            tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]
        else:
            tool_launch_school = None
    except Exception:
        logger.exception('Error getting launch school')

    return tool_launch_school
