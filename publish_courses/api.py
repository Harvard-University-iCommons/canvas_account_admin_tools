# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.views.decorators.http import require_http_methods

from async.models import Process
from lti_permissions.decorators import lti_permission_required
from publish_courses.async_operations import bulk_publish_canvas_sites

logger = logging.getLogger(__name__)


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
