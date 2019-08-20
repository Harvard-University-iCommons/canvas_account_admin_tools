import copy
import logging

from django.core.cache import cache
from django.conf import settings

from icommons_common.canvas_utils import SessionInactivityExpirationRC
from canvas_sdk.methods.admins import list_account_admins
from canvas_sdk.methods.accounts import (
    get_sub_accounts_of_account,
    list_accounts,
)
from canvas_sdk.utils import get_all_list_data


logger = logging.getLogger(__name__)
SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)
CACHE_KEY_ACCOUNTS_BY_USER = 'course_info:canvas:accounts_by_user:{}'
ADMINISTRATOR_ROLES = {'School Liaison', 'SchoolLiaison', 'Account Admin', 'AccountAdmin'}


def get_administered_school_accounts(canvas_user_id, allowed_roles=ADMINISTRATOR_ROLES):
    cache_key = CACHE_KEY_ACCOUNTS_BY_USER.format(canvas_user_id)
    school_accounts = cache.get(cache_key)
    if school_accounts is None:

        # get all accounts
        all_canvas_accounts = get_all_list_data(
            SDK_CONTEXT,
            get_sub_accounts_of_account,
            settings.ICOMMONS_COMMON['CANVAS_ROOT_ACCOUNT_ID'],
            recursive=False)

        # filter so we only have the school accounts
        all_school_accounts = {a['id']: a for a in all_canvas_accounts
                               if (a.get('sis_account_id') or '').startswith('school')}

        # retrieve accounts this user is directly associated with
        assigned_accounts = get_all_list_data(SDK_CONTEXT, list_accounts,
                                              as_user_id=canvas_user_id)

        # for some reason, the role they're assigned is under admins.  grab that
        # role for all the assigned accounts
        allowed_accounts = {}
        for account in assigned_accounts:
            admins = get_all_list_data(SDK_CONTEXT, list_account_admins,
                                       account['id'], user_id=canvas_user_id)

            if allowed_roles.intersection({a['role'] for a in admins}):
                allowed_accounts[account['id']] = account

        # if they're allowed on the root account, they're allowed everywhere
        if settings.ICOMMONS_COMMON['CANVAS_ROOT_ACCOUNT_ID'] in allowed_accounts:
            school_accounts = list(all_school_accounts.values())
        else:
            # filter out the accounts where the user does not have the proper
            # permissions
            school_accounts = [acct for id_, acct in all_school_accounts.items()
                                   if id_ in allowed_accounts]

        logger.debug('%s has access to %s', canvas_user_id,
                     [a['sis_account_id'] for a in school_accounts])
        cache.set(cache_key, school_accounts)
    return school_accounts
