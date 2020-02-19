import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.models import CourseInstance, SiteMap, CourseSite
from lti_permissions.decorators import lti_permission_required

logger = logging.getLogger(__name__)


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
    context = {}

    if course_search_term.isnumeric():
        try:
            ci = CourseInstance.objects.get(course_instance_id=course_search_term)
            context['course_instance'] = ci
        except CourseInstance.DoesNotExist:
            logger.exception('Could not determine the course instance for Canvas '
                             'course instance id %s' % course_search_term)
            messages.error(request, 'Could not find a Course Instance from search term')
    else:
        messages.error(request, 'Search term must be populated and may only be numbers')

    return render(request, 'canvas_site_deletion/index.html', context)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_CANVAS_SITE_DELETION)
@require_http_methods(['GET', 'POST'])
def delete(request, pk):
    try:
        ci = CourseInstance.objects.get(course_instance_id=pk)

        # fetch course sites and site_map data
        try:
            site_maps = SiteMap.objects.filter(course_instance=pk, map_type_id='official')
            for site in site_maps:

                if ('canvas.harvard.edu' in site.course_site.external_id) and (str(ci.canvas_course_id) in site.course_site.external_id):
                    logger.debug('Found Canvas site associated with course : {}'.format(site.course_site.external_id))

                    # Lookup the CourseSite
                    course_site_queryset = CourseSite.objects.filter(course_site_id=site.course_site_id)
                    logger.debug('Number of Courses from CourseSite table is %s', course_site_queryset.count())
                    # 1. delete course site
                    logger.info('User {} is deleting the following course sites {}, from course instance {}'.format(
                        request.user, course_site_queryset.values(), ci.course_instance_id))
                    course_site_queryset.delete()
                    # 2. delete site map
                    logger.info('Deleting site map with the follow details, site map ID:{}, '
                                'course instance ID:{}, course site id:{}, '
                                'map type: {}'.format(site.site_map_id, site.course_instance.course_instance_id,
                                                      site.course_site.course_site_id, site.map_type))
                    site.delete()

        except Exception as e:
            logger.error('Error in deleting Course site or Site map , error:%s' % e)

        # 3. cleanup the canvas course id
        logger.info('Removing canvas course ID:{} from course instance: {}'.format(ci.canvas_course_id,
                                                                                   ci.course_instance_id))
        ci.canvas_course_id = None
        ci.save()

    except Exception as e:
        logger.exception('Could not cleanup  the course instance for Canvas '
                         'course instance id %s.' % pk)
        logger.exception(e)
        messages.error(request, 'Unable to delete cleanup course instance id {}.'.format(pk))

    messages.success(request, "Successfully cleaned up  the Course Site for course_instance_id: {}"
                     .format(pk))

    return render(request, 'canvas_site_deletion/index.html')



