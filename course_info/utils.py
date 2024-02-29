import logging

from canvas_sdk import RequestContext
from canvas_sdk.methods.courses import update_course as canvas_update_course
from django.conf import settings

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)

logger = logging.getLogger(__name__)


def clear_course_sis_id(canvas_course_id):
    """ Makes a Canvas SDK call to set the SIS ID to an empty string for the given Canvas course ID """
    return canvas_update_course(SDK_CONTEXT, canvas_course_id, sis_id='')

