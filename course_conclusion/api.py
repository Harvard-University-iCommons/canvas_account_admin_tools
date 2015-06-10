import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from icommons_common.models import CourseInstance, School, Term


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
    return HttpResponse(json.dumps(school_data),
                        content_type='application/json',
                        status=200)


@login_required
@require_http_methods(['GET'])
def terms(request):
    school_id = request.GET['school_id']
    get_object_or_404(School, pk=school_id)

    # throw an exception if the user isn't allowed to admin this school
    if (not user_is_admin(request) and 
            school_id not in user_allowed_schools(request)):
        raise PermissionDenied()

    query = Term.objects.filter(school_id=school_id).order_by('-academic_year',
                                                              'term_code')
    term_data = [{'term_id': term.term_id,
                  'display_name': term.display_name,
                  'conclude_date': term.conclude_date.strftime('%m/%d/%Y') if term.conclude_date else ''}
                      for term in query]
    return HttpResponse(json.dumps(term_data),
                        content_type='application/json',
                        status=200)


@login_required
@require_http_methods(['GET'])
def courses(request):
    school_id = request.GET['school_id']
    get_object_or_404(School, pk=school_id)

    # throw an exception if the user isn't allowed to admin this school
    if (not user_is_admin(request) and 
            school_id not in user_allowed_schools(request)):
        raise PermissionDenied()

    # throw an exception if that's not a term
    term_id = request.GET['term_id']
    get_object_or_404(Term, pk=term_id) # TODO - include school filter?

    query = CourseInstance.objects.filter(term_id=term_id).order_by('title',
                                                                    'course_id')
    course_data = [{'course_instance_id': course.course_instance_id,
                    'title': course.title,
                    'course_id': course.course_id} for course in query]
    return HttpResponse(json.dumps(course_data),
                        content_type='application/json',
                        status=200)


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
