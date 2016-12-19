# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from canvas_account_admin_tools.utils import _get_schools_context
from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def index(request):
    # prep context data, used to fill filter dropdowns with data targeted
    # to the lti launch's user.
    canvas_user_id = request.LTI['custom_canvas_user_id']
    context = {
        'schools': _get_schools_context(canvas_user_id),
    }
    return render(request, 'publish_courses/index.html', context)


@require_http_methods(['POST'])
def api_publish(request):
    """
    :return: JSON response
    """
    from async.models import Process
    from publish_courses.async_operations import bulk_publish_canvas_sites
    audit_user_id = request.LTI['custom_canvas_user_login_id']
    post_body = json.loads(request.body)
    account = post_body.get('account')
    term = post_body.get('term')
    if not all((account, term)):
        # todo: standardize error type
        resp = {'error': 'InvalidData',
                'detail': 'Both account and term are required'}
        return JsonResponse(resp, status=400)  # BAD REQUEST

    # todo: validate account is ok for this subaccount

    # todo: we need the Canvas term, so faking until frontend delivers year as well
    year = '1900' if term == '99' else '2016'
    sis_term_id = 'sis_term_id:{}-{}'.format(year, term)

    process = Process.enqueue(
        bulk_publish_canvas_sites,
        'bulk_publish_canvas_sites',
        account='sis_account_id:school:{}'.format(account),
        term=sis_term_id,
        audit_user=audit_user_id)

    logger.debug('Enqueued Process job for bulk_publish_canvas_sites: '
                 '{}'.format(process))

    # todo: do we want to do this, or return process.as_dict() in a JsonResponse instead?
    return HttpResponse(process.as_json(), content_type='application/json')


@login_required
@lti_role_required(const.ADMINISTRATOR)
# @lti_permission_required(settings.PERMISSION_PUBLISH_COURSES)
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'publish_courses/partials/' + path, {})
