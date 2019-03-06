import itertools
import logging
from collections import OrderedDict

from django.conf import settings
from django.db import IntegrityError, transaction

from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods.courses import (
    get_single_course_courses as canvas_get_course,
    update_course as canvas_update_course)
from canvas_sdk.methods.sections import (
    cross_list_section,
    de_cross_list_section)
from canvas_sdk.utils import get_all_list_data
from icommons_common.canvas_api.helpers import (
    courses as canvas_api_helper_courses,
    enrollments as canvas_api_helper_enrollments,
    sections as canvas_api_helper_sections
)
from django.contrib import messages

from canvas_sdk import RequestContext

from icommons_common.models import XlistMap, SiteMap, CourseSite

logger = logging.getLogger(__name__)

_xlist_name_modifier = ' [CROSSLISTED - NOT ACTIVE]'
SDK_CONTEXT = RequestContext(**settings.CANVAS_SDK_SETTINGS)


def remove_cross_listing(xlist_id, request):
    """
    If there is an exception in the Canvas SDK, the XREG_MAP record will not
    be deleted.
    """
    instance = XlistMap.objects.get(xlist_map_id=xlist_id)

    _validate_destroy(instance, request)

    secondary_canvas_course = None
    try:
        secondary = instance.secondary_course_instance
        secondary_id = secondary.course_instance_id
        secondary_canvas_course = _get_canvas_course(secondary_id, request)
        canvas_id = secondary_canvas_course.get('id', secondary.canvas_course_id) \
            if secondary_canvas_course else None

        with transaction.atomic(using='coursemanager'):
            _update_site_maps(secondary, canvas_id, request)
            _reset_canvas_course_id(secondary, canvas_id)
            _remove_cross_listing_in_canvas(secondary_id)
            instance.delete()
            messages.success(request, "Successfully decrosslisted primary: {} and secondary: {}"
                             .format(instance.primary_course_instance.course_instance_id, secondary_id))

        # From here on, errors should not roll back the de-cross-listing action
        _remove_xlist_name_modifier(secondary_canvas_course, request)
    except:
        msg = 'Unable to delete cross-listing {}.'.format(xlist_id)
        logger.exception(msg)
        messages.error(request, msg)


def _get_canvas_course(course_sis_id, request):
    course_id = 'sis_course_id:{}'.format(course_sis_id)
    try:
        return canvas_get_course(SDK_CONTEXT, course_id).json()
    except:
        msg = 'Canvas course {} unavailable.'.format(course_id)
        logger.exception('Error during cross-listing: ' + msg)
        messages.error(request, msg)
    return None


def _remove_cross_listing_in_canvas(secondary_id):
    # if the SDK throws an exception the
    # transaction will rollback and nothing will be deleted
    sis_section_id = 'sis_section_id:{}'.format(secondary_id)
    de_cross_list_section(SDK_CONTEXT, sis_section_id)
    logger.info('De-cross-listed Canvas section {}.'.format(sis_section_id))


def _reset_canvas_course_id(secondary, canvas_id):
    # reset the secondary instance to point to the its own canvas course
    secondary.canvas_course_id = canvas_id
    secondary.save(update_fields=['canvas_course_id'])
    logger.info('Reset Canvas course ID for course instance {} to '
                '{}'.format(secondary.course_instance_id, canvas_id))


def _update_site_maps(secondary, canvas_id, request):
    secondary_id = secondary.course_instance_id
    secondary_site_maps = SiteMap.objects.filter(
        course_instance=secondary_id)
    if len(secondary_site_maps):
        map_id_list = [m.site_map_id for m in secondary_site_maps]
        logger.info('Deleting {} existing site maps for course instance '
                    '{}: {}'.format(len(secondary_site_maps),
                                    secondary_id,
                                    map_id_list))
        secondary_site_maps.delete()

    if canvas_id:
        secondary_canvas_course_url = '{}/courses/{}'.format(
            settings.CANVAS_URL, canvas_id)
        secondary_canvas_site = _get_or_create_course_site(
            secondary_canvas_course_url)
        site_map = SiteMap.objects.create(
            course_instance=secondary,
            course_site=secondary_canvas_site,
            map_type_id='official')
        logger.info('Created SiteMap {} to CourseSite {} (external_id = '
                    '{}) for course instance '
                    '{}'.format(site_map.site_map_id,
                                secondary_canvas_site.course_site_id,
                                secondary_canvas_site.external_id,
                                secondary_id))
    else:
        msg = 'The secondary course {} is not associated with a Canvas ' \
              'course. No site mapping was created when ' \
              'de-cross-listing.'.format(secondary_id)
        logger.error(msg)
        messages.error(request, msg)


def _get_or_create_course_site(course_url):
    sites = CourseSite.objects.filter(
        external_id=course_url,
        site_type_id='external')
    if len(sites) > 0:
        return sites[0]
    return CourseSite.objects.create(
        external_id=course_url,
        site_type_id='external')


def _validate_destroy(instance, request):
    primary_id = instance.primary_course_instance.course_instance_id
    secondary_id = instance.secondary_course_instance.course_instance_id
    site_maps = {}
    for course_id in [primary_id, secondary_id]:
        site_maps[course_id] = SiteMap.objects.filter(
            course_instance=course_id)
        if len(site_maps[course_id]) > 1:
            messages.error(request, '{} has multiple site maps.'.format(course_id))


def _remove_xlist_name_modifier(canvas_course, request):
    canvas_course_name = canvas_course.get('name', '')
    if canvas_course_name.endswith(_xlist_name_modifier):
        i = canvas_course_name.rfind(_xlist_name_modifier)
        canvas_course_name = canvas_course_name[:i]
        _update_canvas_course_name(canvas_course['id'], canvas_course_name, request)


def _remove_xlist_name_modifier(canvas_course, request):
    canvas_course_name = canvas_course.get('name', '')
    if canvas_course_name.endswith(_xlist_name_modifier):
        i = canvas_course_name.rfind(_xlist_name_modifier)
        canvas_course_name = canvas_course_name[:i]
        _update_canvas_course_name(canvas_course['id'], canvas_course_name, request)


def _update_canvas_course_name(course_id, course_name, request):
    try:
        response = canvas_update_course(SDK_CONTEXT, course_id,
                                        course_name=course_name)
        logger.info('Updated course name for canvas course {} to be '
                    '{}'.format(course_id, course_name))
        return response
    except:
        msg = 'Name for Canvas course {} could not be ' \
              'updated.'.format(course_id)
        logger.exception('Error during cross-listing: ' + msg)
        messages.error(request, msg)
