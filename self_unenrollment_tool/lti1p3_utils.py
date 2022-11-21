from functools import wraps
from pylti1p3.contrib.django import (DjangoCacheDataStorage, DjangoDbToolConf,
                                     DjangoMessageLaunch, DjangoOIDCLogin)

from logging import getLogger
from django.http import HttpResponseBadRequest

logger = getLogger(__name__)


class LtiResponseBadRequest(HttpResponseBadRequest):
    def __repr__(self) -> str:
        return f'No launch data associated with request'


class CustomDjangoMessageLaunch(DjangoMessageLaunch):
    # Override the default validate_deployment() method from DjangoMessageLaunch since we don't want
    # to have to reconfigure the tool every time someone deploys it in a new course or sub-account.
    def validate_deployment(self):
        return self


def get_message_launch(request, launch_id=None):
    tool_conf = DjangoDbToolConf()
    launch_data_storage = DjangoCacheDataStorage()
    if launch_id:
        message_launch = CustomDjangoMessageLaunch.from_cache(launch_id, request, tool_conf,
                                                            launch_data_storage=launch_data_storage)
    else:
        message_launch = CustomDjangoMessageLaunch(request, tool_conf, launch_data_storage=launch_data_storage)
    return message_launch


def get_launch_url(request):
    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri


def require_lti_launch(func):
    @wraps(func)
    def inner(request, *args, **kwargs):
        launch_id = kwargs.get('launch_id', None)
        message_launch = get_message_launch(request, launch_id=launch_id)
        launch_data = message_launch.get_launch_data()
        if launch_data:
            logger.debug(f'got launch data for request {request.path} ({launch_id})')
        else:
            response = LtiResponseBadRequest()
            logger.error(f'did not get launch data for request {request.path}! ({launch_id})')
            return response

        return func(request, *args, **kwargs)
    return inner
