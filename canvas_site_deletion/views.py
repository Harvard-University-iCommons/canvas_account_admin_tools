import logging
import time

from canvas_sdk import RequestContext
from canvas_sdk.exceptions import CanvasAPIError
from canvas_sdk.methods import courses, sections
from canvas_sdk.methods.courses import \
    get_single_course_courses as canvas_get_course
from canvas_sdk.methods.accounts import (get_sub_accounts_of_account,get_single_account)
from canvas_sdk.utils import get_all_list_data
from coursemanager.models import CourseInstance, CourseSite, SiteMap, Course
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from lti_school_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
@require_http_methods(['GET'])
def index(request):
    context = {}
    return render(request, 'canvas_site_deletion/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
@require_http_methods(['GET', 'POST'])
def lookup(request):
    course_search_term = request.POST.get('course_search_term')
    course_search_term = course_search_term.strip()
    context = {
        'canvas_url': settings.CANVAS_URL,
        'abort': False,
    }

    if course_search_term.isnumeric():
        try:
            ci = CourseInstance.active_and_deleted.get(course_instance_id=course_search_term)
            context['course_instance'] = ci

            if ci.canvas_course_id:
                # get the Canvas course and make sure that the SIS ID matches
                response = courses.get_single_course_courses(SDK_CONTEXT, id=ci.canvas_course_id)
                if response.status_code == 200:
                    cc = response.json()
                else:
                    logger.error(f'Could not retrieve Canvas course {ci.canvas_course_id}')
                    messages.error(request, f'Could not find Canvas course {ci.canvas_course_id}')
                    context['abort'] = True

                if ci.course_instance_id != int(cc['sis_course_id']):
                    logger.error(f'Course instance ID ({course_search_term}) does not match Canvas course SIS ID ({cc["sis_course_id"]}) for Canvas course {ci.canvas_course_id}. Aborting.')
                    messages.error(request, f'Cannot delete course {course_search_term} as it is secondarily-crosslisted with another course. To proceed, undo the existing crosslisting and retry the deletion.')
                    context['abort'] = True
            else:
                logger.error(f'Course instance {ci.course_instance_id} does not have a Canvas course ID set.')
                messages.error(request, f'Course instance {ci.course_instance_id} does not have a Canvas course ID set. Cannot continue.')
                context['abort'] = True

        except CourseInstance.DoesNotExist:
            logger.exception('Could not determine the course instance for Canvas '
                             'course instance id %s' % course_search_term)
            messages.error(request, 'Could not find a Course Instance from search term')
            context['abort'] = True
        except CanvasAPIError:
            logger.exception(f'Could not find Canvas course {ci.canvas_course_id} via Canvas API')
            messages.error(request, f'Could not find Canvas course {ci.canvas_course_id}. Aborting.')
            context['abort'] = True
    else:
        messages.error(request, 'Search term must be populated and may only be numbers')

    return render(request, 'canvas_site_deletion/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
@require_http_methods(['GET', 'POST'])
def delete(request, pk):
    canvas_course_id = None
    try:
        ci = CourseInstance.active_and_deleted.get(course_instance_id=pk)

        canvas_course_id = ci.canvas_course_id
        ts = int(time.time())

        current_tool_launch_account_id = int(request.LTI["custom_canvas_account_id"])

        account_ids = get_account_hierarchy(ci.canvas_course_id)

        if current_tool_launch_account_id not in account_ids:
            logger.error(f'User {request.user} is trying to delete the Canvas site associated with course_instance {pk} but is not in the correct account or sub-account where they have launched the site deletion tool.')
            messages.error(request, f'You must be under the correct account or sub-account in order to delete Canvas course {canvas_course_id} and course_instance {pk}.')
            return render(request, 'canvas_site_deletion/index.html')

        if not canvas_course_id:
            # the course_instance specified doesn't appear to have a Canvas course
            logger.error(f'User {request.user} is trying to delete the Canvas site associated with course_instance {pk} but it has no canvas_course_id')
            messages.error(f'Course instance {pk} does not have an associated Canvas site -- cannot delete.')
            return render(request, 'canvas_site_deletion/index.html')

        # turn off sync_to_canvas and remove canvas_course_id
        logger.info('Step 1/5: turning off sync_to_canvas and removing canvas_course_id {} from course instance {}'.format(ci.canvas_course_id,
                                                                                   ci.course_instance_id))
        ci.sync_to_canvas = 0
        ci.canvas_course_id = None
        ci.save()

        # change the course/section SIS IDs and then delete the courses and sections
        try:
            canvas_course = courses.get_single_course_courses(SDK_CONTEXT, id=canvas_course_id).json()
            canvas_sections = get_all_list_data(SDK_CONTEXT, sections.list_course_sections, canvas_course_id)
            for s in canvas_sections:
                logger.info(f'Step 2/5: changing section {s["id"]} SIS ID to {s["sis_section_id"]}-deleted-{ts}')
                sections.edit_section(
                    SDK_CONTEXT,
                    id=s['id'],
                    course_section_sis_section_id=f'{s["sis_section_id"]}-deleted-{ts}'
                )

            logger.info(f'Step 3/5: changing course {canvas_course_id} SIS ID to {canvas_course["sis_course_id"]}-deleted-{ts} and then deleting the course')
            courses.update_course(SDK_CONTEXT, id=canvas_course_id, course_sis_course_id=f'{canvas_course["sis_course_id"]}-deleted-{ts}')
            logger.info(f'Step 4/5: deleting Canvas course {canvas_course_id}')
            courses.conclude_course(SDK_CONTEXT, id=canvas_course_id, event='delete')
        except CanvasAPIError as e:
            logger.exception(f'Failed to clean up Canvas course/sections for Canvas course ID {canvas_course_id}')

        # fetch course sites and site_map data
        try:
            logger.info(f'Step 5/5: deleting site_map and course_site records associated with course instance {pk}')
            site_maps = SiteMap.objects.filter(course_instance=pk, map_type_id='official')
            for site_map in site_maps:

                if (settings.CANVAS_URL in site_map.course_site.external_id) and (str(canvas_course_id) in site_map.course_site.external_id):
                    logger.debug('Found Canvas site associated with course : {}'.format(site_map.course_site.external_id))

                    # Lookup the CourseSite
                    course_site_queryset = CourseSite.objects.filter(course_site_id=site_map.course_site_id)
                    logger.debug('Number of Courses from CourseSite table is %s', course_site_queryset.count())
                    # 1. delete course site
                    logger.info('User {} is deleting the following course sites {}, from course instance {}'.format(
                        request.user, course_site_queryset.values(), ci.course_instance_id))
                    course_site_queryset.delete()
                    # 2. delete site map
                    logger.info('Deleting site map with the following details, site map ID:{}, '
                                'course instance ID:{}, course site id:{}, '
                                'map type: {}'.format(site_map.site_map_id, site_map.course_instance.course_instance_id,
                                                      site_map.course_site.course_site_id, site_map.map_type))
                    site_map.delete()

        except Exception as e:
            logger.error(f'Error removing associated site_map/course_site from {pk}, error: {e}')

    except Exception as e:
        logger.exception('Could not cleanup  the course instance for Canvas '
                         'course instance id %s.' % pk)
        logger.exception(e)
        messages.error(request, 'Unable to cleanup course instance id {}.'.format(pk))

    messages.success(request, f"Successfully deleted Canvas course {canvas_course_id} and cleaned up course_instance {pk}")

    return render(request, 'canvas_site_deletion/index.html')


def get_account_hierarchy(course_id) -> str:
    """
    Get the list of accounts associated with a given course ID
    """
    account_ids = []

    # use course id to get account id
    canvas_course = canvas_get_course(SDK_CONTEXT, course_id).json()
    canvas_course_account_id = canvas_course["account_id"] 
    account_ids.append(canvas_course_account_id)

    # traverse account hierarchy in both directions
    # first downwards to find sub-accounts
    sub_accounts = get_sub_accounts_of_account(SDK_CONTEXT, canvas_course_account_id).json()
    for sub_account in sub_accounts:
        account_ids.append(sub_account["id"])

    # then upwards to find parent accounts
    while True: 
        account_object = get_single_account(SDK_CONTEXT, canvas_course_account_id).json()
        parent_account_id = account_object.get("parent_account_id")

        if parent_account_id is None:
            break
        account_ids.append(parent_account_id)
        canvas_course_account_id = parent_account_id
    
    return account_ids
