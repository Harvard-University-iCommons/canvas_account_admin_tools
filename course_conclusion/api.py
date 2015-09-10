import datetime
import json
import logging

import pytz
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from icommons_common.models import CourseInstance, School, Term


EASTERN_TZ = pytz.timezone('US/Eastern')
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
    school_data = list(query.values('school_id', 'title_short'))
    return JsonResponse(school_data, safe=False)


@login_required
@require_http_methods(['GET'])
def terms(request):
    # check for required fields in the url
    try:
        assert_required_args_in_or_400({'school_id'}, request.GET)
    except JsonResponseException as r:
        return r

    # make sure the school exists
    school_id = request.GET['school_id']
    try:
        school = get_object_or_404_json(School, school_id=school_id)
    except JsonResponseException as r:
        return r

    # make sure the user is allowed to admin this school
    if (not user_is_admin(request) and 
            school_id not in user_allowed_schools(request)):
        msg = 'Not allowed to administer {}'.format(school.title_short)
        return json_error_response(msg, 403)

    # look up the terms
    years_back = settings.COURSE_CONCLUDE_TOOL.get('years_back', 5)
    query = Term.objects.filter(school_id=school_id,
                                active=1,
                                calendar_year__gt=(
                                    datetime.date.today().year - years_back))
    query = query.order_by('-academic_year', 'term_code')
    term_data = list(query.values('conclude_date', 'display_name', 'term_id'))

    # make sure we're returning just the date
    for term in term_data:
        if term['conclude_date']:
            term['conclude_date'] = term['conclude_date'].date()

    return JsonResponse(term_data, safe=False)


@login_required
@require_http_methods(['GET'])
def courses(request):
    # check for required fields in the url
    try:
        assert_required_args_in_or_400({'school_id', 'term_id'}, request.GET)
    except JsonResponseException as r:
        return r

    # make sure the school exists
    school_id = request.GET['school_id']
    try:
        school = get_object_or_404_json(School, school_id=school_id)
    except JsonResponseException as r:
        return r

    # make sure the user is allowed to admin this school
    if (not user_is_admin(request) and 
            school_id not in user_allowed_schools(request)):
        msg = 'Not allowed to administer {}'.format(school.title_short)
        return json_error_response(msg, 403)

    # make sure the term exists and belongs to the school
    term_id = request.GET['term_id']
    try:
        term = get_object_or_404_json(Term, term_id=term_id)
    except JsonResponseException as r:
        return r
    if term.school != school:
        msg = 'Term {} is not associated with school {}'.format(
                  term_id, school_id)
        return json_error_response(msg, 400)

    # look up the courses
    query = CourseInstance.objects.filter(term_id=term_id).order_by(
                'title', 'course_instance_id')
    course_data = list(query.values('conclude_date', 'course_instance_id',
                                    'title'))

    # make sure we're returning just the date
    for course in course_data:
        if course['conclude_date']:
            course['conclude_date'] = course['conclude_date'].date()

    return JsonResponse(course_data, safe=False)


@login_required
@require_http_methods(['GET'])
def concluded_courses_by_school(request):
    # check for required fields in the url
    try:
        assert_required_args_in_or_400({'school_id'}, request.GET)
    except JsonResponseException as r:
        return r

    school_id = request.GET['school_id']
    filters = {}
    filters['course__school'] = school_id
    query = CourseInstance.objects.filter(**filters).exclude(conclude_date__isnull=True).order_by(
        'title', 'course_id')
    course_data = list(query.values('course_instance_id', 'title', 'conclude_date'))

    for course in course_data:
        if course['conclude_date']:
            course['conclude_date'] = course['conclude_date'].date()
    return JsonResponse(course_data, safe=False)

@login_required
@require_http_methods(['GET'])
def concluded_courses_by_school_term(request):
   # check for required fields in the url
    try:
        assert_required_args_in_or_400({'school_id', 'term_id'}, request.GET)
    except JsonResponseException as r:
        return r

    school_id = request.GET['school_id']
    term_id = request.GET['term_id']

    # look up the concluded courses by school id and term
    filters = {'term_id': term_id}
    filters['course__school'] = school_id
    query = CourseInstance.objects.filter(**filters).exclude(conclude_date__isnull=True).order_by(
        'title', 'course_id')
    course_data = list(query.values('course_instance_id', 'title', 'conclude_date'))

    for course in course_data:
        if course['conclude_date']:
            course['conclude_date'] = course['conclude_date'].date()
    return JsonResponse(course_data, safe=False)

@login_required
@require_http_methods(['PATCH'])
def course(request, course_instance_id):
    # because why would i want django to convert it for me?
    try:
        course_instance_id = int(course_instance_id)
    except ValueError:
        msg = ('Unable to save conclude date, course instance {} is not a number'
                   .format(course_instance_id))
        return json_error_response(msg, 400)

    # parse the body
    try:
        update = json.loads(request.body)
    except ValueError:
        msg = 'Unable to save conclude date, request body is not json'
        return json_error_response(msg, 400)

    # check for required fields in the body
    required = {'course_instance_id', 'conclude_date'}
    try:
        assert_required_args_in_or_400({'course_instance_id', 'conclude_date'},
                                       update)
    except JsonResponseException as r:
        return r

    # make sure the body contains the same course instance
    if update['course_instance_id'] != course_instance_id:
        msg = "Course instance {} in url doesn't match {} from body".format(
                   course_instance_id, update['course_instance_id'])
        return json_error_response(msg, 400)

    # make sure the course exists
    try:
        course = get_object_or_404_json(CourseInstance,
                                        course_instance_id=course_instance_id)
    except JsonResponseException as r:
        return r

    # make sure the user has admin rights to this school
    if (not user_is_admin(request) and 
            course.term.school_id not in user_allowed_schools(request)):
        msg = 'Not allowed to administer {}'.format(
                  course.course.school.title_short)
        return json_error_response(msg, 403)

    # parse it into a date object
    if update['conclude_date']:
        try:
            conclude_date = datetime.datetime.strptime(
                                update['conclude_date'], ISO_FORMAT).date()
        except ValueError:
            msg = '{conclude_date} is not a valid date'.format(**update)
            return json_error_response(msg, 400)
    else:
        conclude_date = None

    # save the course conclude date
    course.conclude_date = conclude_date
    try:
        course.save(update_fields=['conclude_date'])
        # Log when course conclusion date was updated, so that it is easily searchable by splunk if needed
        logger.info("Course conclusion date set to %s for course instance Id=%d by user %s on %s"
                    %(str(conclude_date), course_instance_id, request.user, str(datetime.datetime.now())))
    except Exception as e:
        if conclude_date:
            msg = 'Unable to save the new conclude date {} to'.format(
                      conclude_date)
        else:
            msg = 'Unable to remove the conclude date from'
        msg += ' course "{}"'.format(course.title)
        logger.exception(msg)
        return json_error_response(msg, 500)

    # return the same structure we do from courses()
    course_data = {
        'conclude_date': conclude_date,
        'course_instance_id': course.course_instance_id,
        'title': course.title,
    }
    return JsonResponse(course_data)


class JsonResponseException(JsonResponse, RuntimeError):
    '''
    Mix in an exception with JsonResponse so we can raise a json-formatted
    response from methods, then simply catch and return from views.
    '''
    pass

json_error_response = lambda m,s: JsonResponseException({'error': m}, status=s)


def assert_required_args_in_or_400(required, entity):
    ''' Throws a JsonResponseException if any required args are missing from
    entity. '''
    missing = required.difference(entity.keys())
    if missing:
        msg = 'Required fields {} missing from request'.format(
                  ', '.join(missing))
        raise json_error_response(msg, 400)


def get_object_or_404_json(*args, **kwargs):
    ''' Throws a JsonResponseException if the object cannot be found. '''
    try:
        obj = get_object_or_404(*args, **kwargs)
    except Http404 as e:
        raise json_error_response(unicode(e), 404)
    return obj


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
