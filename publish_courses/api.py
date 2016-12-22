# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.views.decorators.http import require_http_methods

from async.models import Process
from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation
from icommons_common.view_utils import create_json_200_response, \
    create_json_500_response
from publish_courses.async_operations import bulk_publish_canvas_sites

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(['GET'])
def show_summary(request, term_id, account_id):
    """
    Return counts of published courses using the GET parameters given

    :param request:
    :param term_id: The SIS term to count course instances for
    :param account_id: The Canvas account ID for the school to count course instances for
    :return: JSON response containing the course instance counts
    """
    print(" in api_show_summary....")
    year = '1900' if term_id == '99' else '2015'
    sis_term_id = 'sis_term_id:{}-{}'.format(year, term_id)
    sis_account_id = 'sis_account_id:school:{}'.format(account_id)
    print(sis_term_id, sis_account_id)
    result = {}
    try:
        # get published and total number of courses in term
        published_courses = _get_courses_by_published_state(sis_term_id,
                                                            sis_account_id,
                                                            True)
        total_courses = _get_courses_by_published_state(sis_term_id,
                                                        sis_account_id,
                                                        False)
        result= {
            'recordsTotal': len(total_courses),
            'recordsTotalPublishedCourses': len(published_courses),
        }
    except Exception:
        logger.exception("Failed to get published courses summary")
        result['error'] = 'There was a problem counting courses. Please try again.'
        return create_json_500_response(result)

    return create_json_200_response(result)


def _get_courses_by_published_state(sis_term_id, sis_account_id, published):
    op_config = {
        'published': published,
        'account': sis_account_id,
        'term': sis_term_id,
    }
    print(op_config)
    op = BulkCourseSettingsOperation(op_config)
    op._get_canvas_courses()
    courses = op.canvas_courses

    return op.canvas_courses

# todo: lock it down
@require_http_methods(['POST'])
def publish(request):
    audit_user_id = request.LTI['custom_canvas_user_login_id']
    post_body = json.loads(request.body)
    account = post_body.get('account')
    term = post_body.get('term')
    if not all((account, term)):
        # todo: standardize error type, possibly use create_json_*
        resp = {'error': 'InvalidData',
                'detail': 'Both account and term are required'}
        return JsonResponse(resp, status=400)  # BAD REQUEST

    # todo: validate account is ok for this subaccount
    process = Process.enqueue(
        bulk_publish_canvas_sites,
        'bulk_publish_canvas_sites',
        account='sis_account_id:school:{}'.format(account),
        term='sis_term_id:{}'.format(term),
        audit_user=audit_user_id)

    logger.debug('Enqueued Process job for bulk_publish_canvas_sites: '
                 '{}'.format(process))

    # todo: do we want to do this, or return process.as_dict() in a JsonResponse instead?
    return HttpResponse(process.as_json(), content_type='application/json')
