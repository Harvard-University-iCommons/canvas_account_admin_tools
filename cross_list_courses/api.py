
import logging
import json

from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from django_auth_lti.decorators import lti_role_required
from django_auth_lti import const

from icommons_common.view_utils import create_json_200_response, create_json_500_response
from lti_permissions.decorators import lti_permission_required
from icommons_common.models import XlistMap


logger = logging.getLogger(__name__)



@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_ACCOUNT_ADMIN_TOOLS)
@require_http_methods(['GET'])
def list(request):
    """
    Gets the list of cross listed courses

    :param request:
    :return: JSON response containing the list of cross listed courses
    """
    xlist_courses = []
    try:
        xlist_courses = XlistMap.objects.all()

    except Exception as e:
        logger.exception(u"Failed to retrieve cross listed courses with LTI"
                         u" params %s" % json.dumps(request.LTI))
        return None

    return create_json_200_response(xlist_courses)
