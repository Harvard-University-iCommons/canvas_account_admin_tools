import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from canvas_sdk.exceptions import CanvasAPIError
from course_info.canvas import get_administered_school_accounts
from icommons_common.canvas_api.helpers import roles as canvas_api_helpers_roles
from icommons_common.models import UserRole
from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


@login_required
@lti_permission_required('course_info')
@require_http_methods(['GET'])
def index(request):
    canvas_user_id = request.LTI['custom_canvas_user_id']

    # prep context data, used to fill filter dropdowns with data targeted
    # to the lti launch's user.
    context = {
        'schools': _get_schools_context(canvas_user_id),
        'user_roles': _get_canvas_roles(),
    }
    return render(request, 'course_info/index.html', context)


@login_required
@lti_permission_required('course_info')
@require_http_methods(['GET'])
def partials(request, path):
    return render(request, 'course_info/partials/' + path, {})


def _get_canvas_roles():
    """
    Get the list of canvas roles from the canvas root account ('self') and
    create a list in the format the front end wants.
    :return:
    """
    roles = []
    try:
        canvas_roles = canvas_api_helpers_roles.get_roles_for_account_id('self')
        user_roles = UserRole.objects.filter(pk__in=settings.ADD_PEOPLE_TO_COURSE_ALLOWED_ROLES_LIST)
        for role in user_roles:
            label = canvas_roles[role.canvas_role_id]['label']
            roles.append({'roleId': role.role_id,'roleName': label})
    except CanvasAPIError:
        logger.exception("Failed to retrieve roles for the root account from Canvas API")
    except:
        logger.exception("Unhandled exception in _get_canvas_roles; aborting.")

    roles.sort(key=lambda x: x['roleName'])

    return json.dumps(roles)


def _get_schools_context(canvas_user_id):
    accounts = get_administered_school_accounts(canvas_user_id)
    schools = [{
                    'key': 'school',
                    'value': a['sis_account_id'].split(':')[1],
                    'name': a['name'],
                    'query': True,
                    'text': a['name'] + ' <span class="caret"></span>',
                } for a in accounts]
    schools = sorted(schools, key=lambda s: s['name'].lower())
    return json.dumps(schools)
