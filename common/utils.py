import json
import logging
from datetime import datetime

from canvas_api.helpers import accounts as canvas_api_accounts_helper
from canvas_sdk import RequestContext
from canvas_sdk.methods import courses as canvas_api_courses
from canvas_sdk.utils import get_all_list_data
from coursemanager.models import (Course, CourseGroup, CourseInstance,
                                  Department, Term)
from django.conf import settings
from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils import timezone

from canvas_account_admin_tools.models import CanvasSchoolTemplate

logger = logging.getLogger(__name__)

SDK_SETTINGS = settings.CANVAS_SDK_SETTINGS
# make sure the session_inactivity_expiration_time_secs key isn't in the settings dict
SDK_SETTINGS.pop('session_inactivity_expiration_time_secs', None)
SDK_CONTEXT = RequestContext(**SDK_SETTINGS)

CACHE_KEY_CANVAS_SITE_TEMPLATES_BY_SCHOOL_ID = "canvas-site-templates-by-school-id_%s"


def get_school_data_for_user(canvas_user_id, school_sis_account_id=None):
    schools = []
    accounts = canvas_api_accounts_helper.get_school_accounts(
        canvas_user_id,
        canvas_api_accounts_helper.ACCOUNT_PERMISSION_MANAGE_COURSES
    )
    for account in accounts:
        sis_account_id = account['sis_account_id']
        school = {
            'id': account['sis_account_id'],
            'name': account['name']
        }
        if school_sis_account_id and school_sis_account_id == sis_account_id:
            return school
        else:
            schools.append(school)
    return schools

def get_school_data_for_sis_account_id(school_sis_account_id):
    school = None
    if not school_sis_account_id:
        return school
    school_sis_account_id = 'sis_account_id:{}'.format(school_sis_account_id)
    accounts = canvas_api_accounts_helper.get_all_sub_accounts_of_account(
        school_sis_account_id)
    for account in accounts:
        sis_account_id = account['sis_account_id']
        school = {
            'id': account['sis_account_id'],
            'name': account['name']
        }
        if school_sis_account_id == sis_account_id:
            return school
    return school

def get_term_data(term_id):
    term = Term.objects.get(term_id=int(term_id))
    return {
        'id': str(term.term_id),
        'name': term.display_name,
    }

def get_term_data_for_school(school_sis_account_id):
    school_id = school_sis_account_id.split(':')[1]
    year_floor = datetime.now().year - 5  # Limit term query to the past 5 years
    terms = []
    query_set = Term.objects.filter(
        school=school_id,
        active=1,
        calendar_year__gt=year_floor
    ).exclude(
        start_date__isnull=True
    ).exclude(
        end_date__isnull=True
    ).order_by(
        '-end_date', 'term_code__sort_order'
    )
    now = timezone.now()
    current_term_id = None
    for term in query_set:
        # Picks the currently-active term with the earliest end date as the current term
        if term.start_date <= now < term.end_date:
            current_term_id = term.term_id
        terms.append({
            'id': str(term.term_id),
            'name': term.display_name
        })
    return terms, current_term_id

def get_department_data_for_school(school_sis_account_id):
    school_id = school_sis_account_id.split(':')[1]
    departments = []
    query_set = Department.objects.filter(
        school=school_id
    ).order_by(
        'name'
    )

    # Ensure that only departments with active courses are returned
    for department in query_set:
        if is_active_department(department):
            departments.append({
                'id': str(department.department_id),
                'name': department.name
            })

    return departments

def get_course_group_data_for_school(school_sis_account_id):
    school_id = school_sis_account_id.split(':')[1]
    course_groups = []
    query_set = CourseGroup.objects.filter(
        school=school_id
    ).order_by(
        'name'
    )

    # Ensure that only course groups with active courses are returned
    for course_group in query_set:
        if is_active_course_group(course_group):
            course_groups.append({
                'id': str(course_group.course_group_id),
                'name': course_group.name
            })

    return course_groups

def _has_future_end_date_for_course_instance(course_instance: CourseInstance) -> bool:
    date = course_instance.term.end_date
    if not date:
        # if no end_date is set, try using the term's conclude_date
        date = course_instance.term.conclude_date
    if date and date > timezone.now():
        return True
    return False

def _get_courses_from_department(department: Department) -> QuerySet[Course]:
    return Course.objects.filter(department=department)

def _get_courses_from_course_group(course_group: CourseGroup) -> QuerySet[Course]:
    return Course.objects.filter(course_group=course_group)

def _has_active_course_instance(courses: QuerySet[Course]) -> bool:
    if not courses:
        return False
    for course in courses:
        try:
            course_instances = CourseInstance.objects.filter(course=course).select_related("term").filter(term__end_date__gt=timezone.now()).order_by("-term__end_date")
        except CourseInstance.DoesNotExist:
            return False
        most_recent_course_instance = course_instances.first()
        return True if most_recent_course_instance and _has_future_end_date_for_course_instance(most_recent_course_instance) else False

def is_active_department(department: Department) -> bool:
    courses = _get_courses_from_department(department)
    return True if courses and _has_active_course_instance(courses) else False

def is_active_course_group(course_group: CourseGroup) -> bool:
    courses = _get_courses_from_course_group(course_group)
    return True if courses and _has_active_course_instance(courses) else False

def get_canvas_site_templates_for_school(school_id):
    """
    Get the Canvas site templates for the given school. First check the cache, if not found construct
    the Canvas site template dictionary list by querying CanvasSchoolTemplate and the courses Canvas API
    to get the Canvas template site name.

    :param school_id:
    :return: List of dicts containing data for Canvas site templates for the given school
    """
    cache_key = CACHE_KEY_CANVAS_SITE_TEMPLATES_BY_SCHOOL_ID % school_id
    templates = cache.get(cache_key)
    if templates is None:
        templates = []
        for t in CanvasSchoolTemplate.objects.filter(school_id=school_id):
            try:
                canvas_course_id = t.template_id
                course = get_all_list_data(
                    SDK_CONTEXT,
                    canvas_api_courses.get_single_course_courses,
                    canvas_course_id,
                    None
                )
                templates.append({
                    'canvas_course_name': course['name'],
                    'canvas_course_id': canvas_course_id,
                    'canvas_course_url': "%s/courses/%d" % (settings.CANVAS_URL, canvas_course_id),
                    'is_default': t.is_default
                })
            except Exception as e:
                logger.warn('Failed to retrieve Canvas course for template/course ID {}: {}'.format(t.template_id, e))

        logger.debug("Caching canvas site templates for school_id %s %s", school_id, json.dumps(templates))
        cache.set(cache_key, templates)

    return templates

def get_canvas_site_template(school_id, template_canvas_course_id):
    """
    Get the Canvas site template given the school and the Canvas template site canvas course id.

    :param school_id:
    :param template_canvas_course_id:
    :return: Dict containing data for the Canvas site template
    """
    for t in get_canvas_site_templates_for_school(school_id):
        if t['canvas_course_id'] == template_canvas_course_id:
            return t
    return None
