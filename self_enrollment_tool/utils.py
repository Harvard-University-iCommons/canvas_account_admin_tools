import logging

from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.external_tools import (create_external_tool_courses,
                                               list_external_tools_courses)
from canvas_sdk.utils import get_all_list_data
from django.conf import settings
from icommons_common.canvas_api.helpers import \
    roles as canvas_api_helpers_roles
from icommons_common.models import UserRole

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)


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


def install_unenrollment_tool(course_instance_id, client_id):
    # make sure that the unenrollment tool is installed


    if not client_id:
        raise Exception('Could not install the self-unenrollment tool into the Canvas course site: the tool client_id is missing.')

    # client_id is in global format (e.g. 18750000000000001)
    # convert it to local format so we can compare it to the developer_key_id
    local_client_id = int(client_id) % 10000000000000

    # first, check to see if this tool is already installed
    installed_tools = get_all_list_data(SDK_CONTEXT, list_external_tools_courses, course_id=f'sis_course_id:{course_instance_id}')
    is_installed = False
    for t in installed_tools:
        if t['version'] == '1.3':
            developer_key_id = t['developer_key_id']
            # if the client_id and the developer_key_id match, the tool is already installed
            # TBD: compare the global client_id to the local developer_key_id
            logger.debug(f'comparing {developer_key_id} to {local_client_id}')
            if int(developer_key_id) == local_client_id:
                # the tool is already installed
                logger.info(f'external tool ({client_id}/{developer_key_id}) was already installed in course {course_instance_id}')
                is_installed = True
                return 'already_installed'

    if not is_installed:
        logger.debug(f'local client id {local_client_id} (from {client_id}) was not found in installed tools - installing it now')
        result = create_external_tool_courses(SDK_CONTEXT, course_id=f'sis_course_id:{course_instance_id}', client_id=client_id)
        if result.status_code == 200:
            logger.info(f'successfully installed external tool {client_id} into course {course_instance_id}')
            return 'installed'
        else:
            logger.error(f'failed to install external tool {client_id} into course {course_instance_id}: {result.text}')
            raise Exception(f'Could not install the self-unenrollment tool into the Canvas site for course {course_instance_id}')
