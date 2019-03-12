import logging

from django.conf import settings

from canvas_sdk.methods.courses import update_course as canvas_update_course
from icommons_common.canvas_utils import SessionInactivityExpirationRC

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)
logger = logging.getLogger(__name__)


def clear_course_sis_id(canvas_course_id):
    """ Makes a Canvas SDK call to set the SIS ID to an empty string for the given Canvas course ID """
    return canvas_update_course(SDK_CONTEXT, canvas_course_id, course_sis_course_id='')

