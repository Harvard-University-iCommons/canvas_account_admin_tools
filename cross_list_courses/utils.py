import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction

from canvas_sdk.methods.courses import (
    get_single_course_courses as canvas_get_course,
    update_course as canvas_update_course)
from canvas_sdk.methods.sections import (
    cross_list_section,
    de_cross_list_section)
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import XlistMap, SiteMap, CourseSite, CourseInstance

logger = logging.getLogger(__name__)

_xlist_name_modifier = ' [CROSS-LISTED - NOT ACTIVE]'
SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

_messages = {
        'ci_does_not_exist': '{id} does not exist.',
        'multiple_site_maps': "Course instance {id} has multiple course sites associatedwith it, and this tool isn't able to handle that situation. Please contact academictechnology@harvard.edu for assistance.",
        'primary_same_as_secondary': 'The primary course {p_id} cannot be the same as secondary course {s_id}.',
        'not_synced': "The primary course ({p_id}) doesn't have a Canvas site, but when one is created the secondary course ({s_id}) will be cross-listed with it.",
        'primary_already_xlisted': '{s_id} is currently cross-listed as a '
                                   'secondary with {p_id} as a primary.',
        'reverse': 'Unable to create a cross-listing: a reverse pairing for these IDs (primary: {s_id}, '
                   'secondary: {p_id}) already exists.',
        'secondary_already_primary': '{p_id} is currently cross-listed as a '
                                     'primary course with {s_id} as its '
                                     'secondary.',
        'secondary_already_secondary': '{s_id} is currently cross-listed with '
                                       '{p_id} as its primary.',
        'invalid input': 'Invalid value for primary {p_id} or secondary {p_id} '
    }


def remove_cross_listing(xlist_id, request):
    """
    If there is an exception in the Canvas SDK, the XREG_MAP record will not
    be deleted.
    """
    instance = XlistMap.objects.get(xlist_map_id=xlist_id)

    _validate_destroy(instance, request)

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
            messages.success(request, "Successfully de-cross-listed primary: {} and secondary: {}"
                             .format(instance.primary_course_instance.course_instance_id, secondary_id))

        # From here on, errors should not roll back the de-cross-listing action
        _remove_xlist_name_modifier(secondary_canvas_course, request)
    except Exception as e:
        msg = 'Unable to delete cross-listing {}.'.format(xlist_id)
        logger.exception(msg)
        logger.exception(e)
        messages.error(request, msg)


def create_crosslisting_pair(primary_id, secondary_id, request):

    try:
        # Validate the primary and secondary values before processing.
        # Validation messages are transmitted to the view by this method
        primary_id = primary_id.strip()
        secondary_id = secondary_id.strip()
        is_valid = validate_inputs(primary_id, secondary_id, request)
        
        if is_valid:
            primary = CourseInstance.objects.get(course_instance_id=primary_id)
            canvas_id = None

            # TLT-2618: check that primary is currently syncing to Canvas
            # If the setting is false, show a warning but continue to process the request
            if primary.sync_to_canvas == 0:
                msg_context = {'p_id': primary_id, 's_id': secondary_id}
                msg = msg_for_error('not_synced', msg_context)
                messages.warning(request, msg)
            else:
                primary_canvas_course = _get_canvas_course(primary_id, request)
                canvas_id = primary_canvas_course.get('id', primary.canvas_course_id) \
                    if primary_canvas_course else primary.canvas_course_id

            if not canvas_id:
                logger.debug('The primary course {} is not associated with a Canvas course.'.format(primary_id))

            secondary = CourseInstance.objects.get(course_instance_id=secondary_id)
            secondary_canvas_course = _get_canvas_course(secondary_id, request)

            sec_canvas_id = secondary_canvas_course.get('id', secondary.canvas_course_id) \
                if secondary_canvas_course else secondary.canvas_course_id

            created_by = request.user

            # this step can raise an unhandled error, aborting the process and
            # returning a non-201 error response
            _update_course_db(primary, secondary, canvas_id, created_by)

            # these steps will not abort the process, and a 201 response will be
            # returned, possibly with error details
            if canvas_id and sec_canvas_id:
                _update_canvas_cross_listing(primary_id, secondary_id, request)
                _update_canvas_course_names(primary_canvas_course, secondary_canvas_course, request)

            messages.success(request, "Successfully cross-listed primary: {} and secondary: {}"
                             .format(primary_id, secondary_id))

    except Exception as e:

        msg = 'Unable to create cross-listing for primary {}, secondary {}.'.format(primary_id, secondary_id)
        logger.exception(msg)
        logger.exception(e)
        messages.error(request, msg)


def _get_canvas_course(course_sis_id, request):
    course_id = 'sis_course_id:{}'.format(course_sis_id)
    try:
        return canvas_get_course(SDK_CONTEXT, course_id).json()
    except Exception as e:
        msg = 'Canvas course {} unavailable.'.format(course_id)
        logger.info('Error during cross-listing: ' + msg)
        logger.info(e)
    return None


def _remove_cross_listing_in_canvas(secondary_id):
    # if the SDK throws an exception, log the error but continue processing (TLT-3788)
    sis_section_id = 'sis_section_id:{}'.format(secondary_id)
    try:
        de_cross_list_section(SDK_CONTEXT, sis_section_id)
    except Exception as e:
        logger.info('Error during canvas course cleanup for section {}.'.format(sis_section_id))
        logger.info(e)

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
        # log the message but proceed with the delete process
        logger.info(msg)


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
    if canvas_course:
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


def _update_course_db(primary, secondary, canvas_id, created_by):
    try:
        with transaction.atomic(using='coursemanager'):
            _create_xlist_map(primary, secondary, created_by)
            if canvas_id:
                _update_canvas_course_id(primary, secondary, canvas_id)
                _update_course_sites(primary, secondary)

    except Exception as e:
        msg = 'Unable to create cross-listing for {}, {}. There was an error ' \
              'accessing the database.'.format(primary.course_instance_id, secondary.course_instance_id)

        logger.exception(msg)
        logger.exception(e)
        raise Exception(msg)


def _create_xlist_map(primary, secondary, created_by):
    # Save the mapping
    xlist_map = XlistMap(primary_course_instance=primary, secondary_course_instance=secondary,
                         last_modified_by=created_by)
    xlist_map.save()

    # Set sync to Canvas of primary
    # primary = xlist_map.primary_course_instance
    primary.sync_to_canvas = 1
    primary.save(update_fields=['sync_to_canvas'])
    logger.info(
        'Created XlistMap {} and ensured sync_to_canvas=1 for primary '
        'course instance {}'.format(xlist_map.xlist_map_id,
                                    primary.course_instance_id))


def _update_canvas_cross_listing(primary_sis_id, secondary_sis_id, request):
    # The sections for the two courses should exist in the new primary
    # course. Neither of these sections should exist in the former
    # primary course (though there may still appear to be manually
    # created sections there that we will have to clean up manually).
    secondary_section_id = 'sis_section_id:{}'.format(secondary_sis_id).strip()
    primary_course_id = 'sis_course_id:{}'.format(primary_sis_id).strip()

    try:
        response = cross_list_section(SDK_CONTEXT, secondary_section_id,
                                      primary_course_id)
        logger.info(
            'Cross-listed secondary Canvas section {} to primary Canvas '
            'course {}'.format(secondary_section_id, primary_course_id))
        return response
    except:
        msg = 'Unable to currently cross-list Canvas section {} in Canvas course {}' \
            .format(secondary_section_id,
                    primary_course_id, )
        logger.exception(msg)
        messages.warning(request, msg)


def _update_canvas_course_names(primary, secondary, request):
    # The newly cross-listed secondary course should have the customary
    # [CROSS-LISTED - NOT ACTIVE] in its title

    if primary and primary.get('id'):
        _remove_xlist_name_modifier(primary, request)
    if secondary and secondary.get('id'):
        _append_xlist_name_modifier(secondary, request)


def _append_xlist_name_modifier(canvas_course, request):
    canvas_course_name = canvas_course.get('name', '')
    if not canvas_course_name.endswith(_xlist_name_modifier):
        canvas_course_name += _xlist_name_modifier
        _update_canvas_course_name(canvas_course['id'], canvas_course_name, request)


def _update_canvas_course_id(primary, secondary, canvas_id):
    # update the course instances to point to the primary canvas course

    if primary.canvas_course_id != canvas_id:
        logger.warning(
            'Course instance {} has missing/wrong canvas_course_id; '
            'old:{} new:{}'.format(primary.course_instance_id,
                                   primary.canvas_course_id, canvas_id))
    for course in [primary, secondary]:
        if course.canvas_course_id != canvas_id:
            course.canvas_course_id = canvas_id
            course.save(update_fields=['canvas_course_id'])

            logger.info(
                'Updated Canvas course ID for course instance {} to '
                '{}'.format(course.course_instance_id, canvas_id))


def _update_course_sites(primary, secondary):
    # if no SiteMap exists for primary to its Canvas Site, create one and
    # point it to its Canvas site (note: we will create a new CourseSite,
    # and not worry about any existing CourseSites with the same
    # external_id)

    official_canvas_site = None
    other_primary_site_map = None
    primary_canvas_course_url = '{}/courses/{}'.format(
        settings.CANVAS_URL, primary.canvas_course_id)

    primary_sites = primary.sites.all()
    secondary_sites = secondary.sites.all()

    if len(primary_sites) == 0:
        pass  # official_canvas_site needs to be created below
    elif len(primary_sites) == 1:

        primary_site = primary_sites[0]
        site_map = SiteMap.objects.get(course_instance=primary)
        if primary_site.external_id == primary_canvas_course_url:
            official_canvas_site = primary_site
            if site_map.map_type_id != 'official':
                site_map.map_type_id = 'official'
                site_map.save(update_fields=['map_type'])
                logger.info(
                    'Updated existing SiteMap {} for primary course '
                    'instance {} to be official'.format(
                        site_map.site_map_id, primary.course_instance_id))
        elif settings.CANVAS_URL in primary_site.external_id:

            # note: this differs from canvas_integration.fix_external_links
            # command behavior, which only marks the existing Canvas link
            # as unofficial
            primary_site.external_id = primary_canvas_course_url
            primary_site.save(update_fields=['external_id'])
            if site_map.map_type_id != 'official':
                site_map.map_type_id = 'official'
                site_map.save(update_fields=['map_type'])
                logger.info(
                    'Updated existing SiteMap {} for primary course '
                    'instance {} to be official'.format(
                        site_map.site_map_id, primary.course_instance_id))
            logger.info(
                'Updated existing CourseSite {} for primary course '
                'instance {} to point to primary canvas site {}'.format(
                    primary_site.course_site_id,
                    primary.course_instance_id,
                    primary_canvas_course_url))
        else:

            logger.info(
                'Primary course instance {} has a single, non-Canvas '
                'site map: {}'.format(primary.course_instance_id,
                                      primary_site.external_id))
            other_primary_site_map = primary_site
    else:

        msg = 'Primary course instance {} unexpectedly has more than ' \
              'one site map.'.format(primary.course_instance_id)
        logger.exception(msg)

    if official_canvas_site is None:
        official_canvas_site = CourseSite.objects.create(
            external_id=primary_canvas_course_url,
            site_type_id='external')
        site_map = SiteMap.objects.create(
            course_instance=primary,
            course_site=official_canvas_site,
            map_type_id='official')
        logger.info('Created SiteMap {} to CourseSite {} (external_id = '
                    '{}) for primary course instance '
                    '{}'.format(site_map.site_map_id,
                                official_canvas_site.course_site_id,
                                official_canvas_site.external_id,
                                primary.course_instance_id))

    # Secondary will inherit the primary's site maps (at this point there
    # should be only be one Canvas site map and possibly one other site map)

    if len(secondary_sites) == 0:

        site_map = SiteMap.objects.create(
            course_instance=secondary,
            course_site=official_canvas_site,
            map_type_id='official')
        logger.info('Created SiteMap {} to CourseSite {} (external_id = '
                    '{}) for secondary course instance '
                    '{}'.format(site_map.site_map_id,
                                official_canvas_site.course_site_id,
                                official_canvas_site.external_id,
                                secondary.course_instance_id))
    elif len(secondary_sites) == 1:

        site_map = SiteMap.objects.get(course_instance=secondary)
        site_map.course_site = official_canvas_site
        site_map.map_type_id = 'official'
        site_map.save(update_fields=['course_site', 'map_type'])
        logger.info('Created SiteMap {} to CourseSite {} (external_id = '
                    '{}) for secondary course instance '
                    '{}'.format(site_map.site_map_id,
                                official_canvas_site.course_site_id,
                                official_canvas_site.external_id,
                                secondary.course_instance_id))
    else:

        msg = 'Secondary course instance {} unexpectedly has more than ' \
              'one site map.'.format(secondary.course_instance_id)
        logger.exception(msg)
        # raise ValidationError(msg)

    if other_primary_site_map is not None:
        site_map = SiteMap.objects.create(
            course_instance=secondary,
            course_site=other_primary_site_map,
            map_type_id='map_type')
        logger.info(
            'Copied over SiteMap {} from primary course instance {} to '
            'secondary course instance '
            '{}'.format(site_map.site_map_id,
                        primary.course_instance_id,
                        secondary.course_instance_id))


def msg_for_error(msg_key, context):
    msg = _messages.get(msg_key, '')
    if msg and isinstance(context, dict):
        msg = msg.format(**context)
        return msg


def validate_inputs(primary_id, secondary_id, request):
    """
    Validates the given primary and secondary inputs.
    If any of the conditions fail, return False and do not continue to process the request
    """

    if primary_id == secondary_id:
        msg_context = {'s_id': secondary_id, 'p_id': primary_id}
        msg = msg_for_error('primary_same_as_secondary', msg_context)
        messages.error(request, msg)
        return False

    try:
        primary_ci = CourseInstance.objects.get(pk=primary_id)
        secondary_ci = CourseInstance.objects.get(pk=secondary_id)
    except Exception as e:
        msg_context = {'p_id': primary_id, 's_id': secondary_id}
        msg = msg_for_error('invalid input', msg_context)
        messages.error(request, msg)
        logger.info(e)
        return False

    # 1. reverse check
    reverse_xlist = XlistMap.objects.filter(
        secondary_course_instance=primary_id,
        primary_course_instance=secondary_id
    ).values_list('primary_course_instance', 'secondary_course_instance')
    if len(reverse_xlist) > 0:
        msg_context = {'p_id': primary_id, 's_id': secondary_id}
        msg = msg_for_error('reverse', msg_context)
        messages.error(request, msg)
        return False

    # 2. check to make sure that the secondary instance is not already
    # cross-listed with a different primary.
    # Note: Using the data from the first record found
    existing_xlist = XlistMap.objects.filter(
        secondary_course_instance=secondary_id
    ).values_list('primary_course_instance', 'secondary_course_instance')
    if len(existing_xlist) > 0:
        msg_context = {'s_id': secondary_id, 'p_id': existing_xlist[0][0]}
        msg = msg_for_error('secondary_already_secondary', msg_context)
        messages.error(request, msg)
        return False

    # 3. check to make sure that the primary instance is not a secondary to
    #  any instance
    existing_xlist = XlistMap.objects.filter(
        secondary_course_instance=primary_id
    ).values_list('primary_course_instance', 'secondary_course_instance')
    if len(existing_xlist) > 0:
        msg_context = {'p_id': existing_xlist[0][0], 's_id': primary_id}
        msg = msg_for_error('primary_already_xlisted', msg_context)
        messages.error(request, msg)
        return False

    # 4. check to make sure that the secondary is not already a primary to
    # another instance
    existing_primary = XlistMap.objects.filter(
        primary_course_instance=secondary_id
    ).values_list('primary_course_instance', 'secondary_course_instance')
    if len(existing_primary) > 0:
        msg_context = {'p_id': secondary_id, 's_id': existing_primary[0][1]}
        msg = msg_for_error('secondary_already_primary', msg_context)
        messages.error(request, msg)
        return False

    # 5. TLT-2900: only allow cross-listings for cases where no complex
    # site map relationship exists.
    site_maps = {}
    for course_id in [primary_id, secondary_id]:
        site_maps[course_id] = SiteMap.objects.filter(
            course_instance=course_id)
        if len(site_maps[course_id]) > 1:
            msg = msg_for_error('multiple_site_maps', {'id': course_id})
            messages.error(request, msg)
            return False

    return True
