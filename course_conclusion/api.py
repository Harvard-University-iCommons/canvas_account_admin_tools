import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from icommons_common.models import CourseInstance, School, Term


ISO_FORMAT = '%Y-%m-%d'
logger = logging.getLogger(__name__)


@login_required
@require_http_methods(['GET'])
def schools(request):
    query = School.objects.filter(active=1)

    # filter down to just the user's allowed schools if the user isn't an admin
    if not user_is_admin(request):
        query = query.filter(school_id__in=user_allowed_schools(request))

    query = query.order_by('title_short')
    school_data = [{'school_id': school.school_id,
                    'title_short': school.title_short} for school in query]
    return JsonResponse(school_data, safe=False)


@login_required
@require_http_methods(['GET'])
def terms(request):
    school_id = request.GET['school_id']
    get_object_or_404(School, school_id=school_id)

    # throw an exception if the user isn't allowed to admin this school
    if (not user_is_admin(request) and 
            school_id not in user_allowed_schools(request)):
        raise PermissionDenied()

    query = Term.objects.filter(school_id=school_id).order_by('-academic_year',
                                                              'term_code')
    term_data = [{
        'conclude_date': term.conclude_date,
        'display_name': term.display_name,
        'term_id': term.term_id,
    } for term in query]
    return JsonResponse(term_data, safe=False)


@login_required
@require_http_methods(['GET'])
def courses(request):
    school_id = request.GET['school_id']
    get_object_or_404(School, school_id=school_id)

    # throw an exception if the user isn't allowed to admin this school
    if (not user_is_admin(request) and 
            school_id not in user_allowed_schools(request)):
        raise PermissionDenied()

    # throw an exception if that's not a term
    term_id = request.GET['term_id']
    get_object_or_404(Term, term_id=term_id)

    query = CourseInstance.objects.filter(term_id=term_id).order_by('title',
                                                                    'course_id')
    course_data = [{
        'conclude_date': course.conclude_date,
        'course_id': course.course_id,
        'course_instance_id': course.course_instance_id,
        'title': course.title,
    } for course in query]
    return JsonResponse(course_data, safe=False)


@login_required
@require_http_methods(['PATCH'])
def course(request, course_instance_id):
    # because why would i want django to convert it for me?
    try:
        course_instance_id = int(course_instance_id)
    except ValueError as e:
        msg = ('Unable to save conclude date, course instance {} is not a number'
                   .format(course_instance_id))
        logger.exception(msg)
        return JsonResponse({'error': msg}, status=400)

    # make sure the body contains the same course instance
    try:
        update = json.loads(request.body)
        if update['course_instance_id'] != course_instance_id:
            msg = 'Course instance {} in url doesn\'t match {} from body'.format(
                      course_instance_id, update['course_instance_id'])
            logger.error(msg)
            return JsonResponse({'error': msg}, status=400)
    except Exception as e:
        msg = 'Unable to read conclude date from request body'
        logger.exception(msg)
        return JsonResponse({'error': msg}, status=400)

    # now make sure the course exists
    course = get_object_or_404(CourseInstance,
                               course_instance_id=course_instance_id)

    # make sure the user has admin rights to this school
    if (not user_is_admin(request) and 
            course.school_id not in user_allowed_schools(request)):
        return JsonResponse({'error': 'Not allowed to administer {}'.format(
                                          course.course.school.name)},
                            status=403)

    # parse it into a date object
    if update['conclude_date']:
        conclude_date = datetime.datetime.strptime(
                            update['conclude_date'], ISO_FORMAT).date()
    else:
        conclude_date = None

    # save the course conclude date
    course.conclude_date = conclude_date
    try:
        course.save(update_fields=['conclude_date'])
    except Exception as e:
        if conclude_date:
            msg = 'Unable to save the new conclude date {} to'.format(
                      conclude_date)
        else:
            msg = 'Unable to remove the conclude date from '
        msg += ' course "{}"'.format(course.title)
        logger.exception(msg)
        return JsonResponse({'error': msg}, status=500)


    # return the same structure we do from courses()
    course_data = {
        'course_instance_id': course.course_instance_id,
        'title': course.title,
        'course_id': course.course_id,
        'conclude_date': course.conclude_date,
    }
    return JsonResponse(course_data)


def user_is_admin(request):
    user_groups = set(request.session['USER_GROUPS'])
    admin_group = set()
    if 'ADMIN_GROUP' in settings.TERM_TOOL:
        admin_group.add(settings.TERM_TOOL['ADMIN_GROUP'])
    return bool(admin_group & user_groups)


def user_allowed_schools(request):
    user_groups = set(request.session['USER_GROUPS'])
    allowed_by_group = settings.TERM_TOOL.get('ALLOWED_GROUPS', {})
    user_allowed_groups = user_groups.intersection(allowed_by_group.keys())
    return [school for group, school in allowed_by_group
                if group in user_allowed_groups]
