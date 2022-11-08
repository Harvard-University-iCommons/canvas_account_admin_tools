import logging

from canvas_sdk.exceptions import CanvasAPIError
from django.conf import settings
from icommons_common.canvas_api.helpers import \
    roles as canvas_api_helpers_roles
from icommons_common.models import UserRole

logger = logging.getLogger(__name__)

def get_canvas_roles():
    logger.debug(f"called _get_canvas_roles()")
    roles = []
    try:
        canvas_roles = canvas_api_helpers_roles.get_roles_for_account_id('self')
        user_roles = UserRole.objects.filter(pk__in=settings.SELF_ENROLLMENT_TOOL_ROLES_LIST)
        for role in user_roles:
            label = canvas_roles[role.canvas_role_id]['label']
            roles.append({'roleId': role.role_id, 'roleName': label})
    except CanvasAPIError:
        logger.exception("Failed to retrieve roles for the root account from Canvas API")
        return None
    except Exception:
        logger.exception("Unhandled exception in _get_canvas_roles; aborting.")
        return None

    roles.sort(key=lambda x: x['roleName'])
    logger.debug(f"returning roles: {roles}")
    return roles
