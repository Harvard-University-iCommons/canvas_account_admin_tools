from django.http import QueryDict
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from icommons_common.canvas_utils import *
from django.conf import settings
from functools import wraps
import logging

CAS_LOGOUT_URL = settings.CAS_LOGOUT_URL

logger = logging.getLogger(__name__)


def check_user_id_integrity(login_id_required=True, missing_login_id_redirect_url=None):
    """
    Decorator to check if tool user is the same as the Canvas user
    Usage: decorate the View with check_user_id_integrity() or add arguments as needed
           * Note the parentheses are required even when no arguments are passed,
             as this is actually a decorator factory, not a bare decorator.
    """
    def decorator(view_func):
        @wraps(view_func)
        @require_http_methods(['GET'])
        def wrapper(request, *args, **kwargs):
            # Check for 'canvas_login_id', which will be passed in by shop.js
            # on the Canvas instance. If it's not present the code will skip this
            # block and continue on. If it's present, verify that it matches the
            # user_id in the tool. If there is a mismatch, send user to pin logout
            # (this is the current security patch, maybe modified with a better solution.)

            # check for canvas_login_id parameter; this decorator could be used
            # for POST and GET 

            # canvas_login_id is the 'login_id' attribute from the Canvas
            # user profile. It is essentially the Canvas sis_user_id (e.g. HUID)
            canvas_login_id = request.GET.get('canvas_login_id')
            if not canvas_login_id:
                logger.debug('canvas_login_id not a GET parameter, trying POST')
                canvas_login_id = request.POST.get('canvas_login_id')

            if canvas_login_id:
                user_id = request.user.username
                logger.debug('user id integrity check: user in tool=%s, '
                             'canvas_login_id from request == %s' % (user_id, canvas_login_id))

                if str(user_id) != str(canvas_login_id):
                    logger.error('user integrity mismatch: user in tool=%s, canvas_login_id from request=%s. '
                                 'Logging out the user from CAS' % (user_id, canvas_login_id))
                    return redirect(CAS_LOGOUT_URL)
            elif login_id_required:
                # canvas_login_id is required to access the calling function
                # but was not found in the request parameters; redirect to
                # specified URL or to CAS logout if URL was not provided by
                # calling function
                logger.info('user integrity check: login id is required but was not found in request.')
                if missing_login_id_redirect_url:
                    logger.debug('user integrity check: redirecting to %s' % missing_login_id_redirect_url)
                    return redirect(missing_login_id_redirect_url)
                else:
                    logger.debug('user integrity check: Logging out the user from CAS.')
                    return redirect(CAS_LOGOUT_URL)
            # User integrity check passed: tool user is the same as the Canvas user, continue
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
