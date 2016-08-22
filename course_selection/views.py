from __future__ import unicode_literals
from urllib import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from icommons_common.models import CourseInstance


@require_http_methods(['GET'])
def locate_course(request):
    """
    Attempts to redirect to a specific course in the Harvard SIS (Campus
    Solutions) based on a course instance ID passed as a GET query parameter.
    If the course cannot be found, redirects to the generic course lookup page
    in the Harvard SIS application.
    """
    sis_base_url = settings.COURSE_SELECTION['sis_base_url']
    cid = request.GET.get('course_instance_id')
    ci = None

    if cid:
        try:
            ci = CourseInstance.objects.get(course_instance_id=cid)
        except:
            pass  # redirect to generic search url, below

    if ci and ci.cs_class_number and ci.term.cs_strm:
        base_params = settings.COURSE_SELECTION['sis_query_add_course_params']
        course_params = {
            'SearchReqJSON': '{{"SearchText":"(CLASS_NBR:{}) (STRM:{})"}}'.format(
                ci.cs_class_number, ci.term.cs_strm)
        }
        course_params.update(base_params)
        add_course_url = '{}?{}'.format(sis_base_url, urlencode(course_params))
        return redirect(add_course_url)

    search_params = settings.COURSE_SELECTION['sis_query_search_params']
    generic_search_url = '{}?{}'.format(sis_base_url, urlencode(search_params))
    return redirect(generic_search_url)
