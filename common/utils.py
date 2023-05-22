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
from django.db.models import Exists, OuterRef
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

def get_department_data_for_school(school_sis_account_id: str) -> list:
    """
    Returns a list of validated departments for a given school.
    This validation is done to prevent legacy departments from being displayed in the UI.
    """

    school_id = school_sis_account_id.split(':')[1]
    departments = []
    query_set = Department.objects.filter(
        school=school_id
    ).order_by(
        'name'
    )

    validated_departments = _get_departments_with_future_ci_term_end_date(query_set)

    for department in validated_departments:
        if department.has_future_course_instance:
            departments.append({
                'id': str(department.department_id),
                'name': department.name
            })

    return departments

def get_course_group_data_for_school(school_sis_account_id: str) -> list:
    """
    Returns a list of validated coursegroups for a given school.
    This validation is done to prevent legacy course groups from being displayed in the UI.
    """
    school_id = school_sis_account_id.split(':')[1]
    course_groups = []
    query_set = CourseGroup.objects.filter(
        school=school_id
    ).order_by(
        'name'
    )

    validated_coursegroups = _get_coursegroups_with_ci_future_end_date(query_set)

    for coursegroup in validated_coursegroups:
        if coursegroup.has_future_course_instance:
            course_groups.append({
                'id': str(coursegroup.course_group_id),
                'name': coursegroup.name
            })

    return course_groups


def _get_departments_with_future_ci_term_end_date(departments: QuerySet[Department]) -> QuerySet[Department]:
    """
    Returns a QuerySet of Departments that have at least one Course with a CourseInstance with a Term end_date
    in the future.
    """
    future_course_instance_exists = CourseInstance.objects.filter(
        course__department=OuterRef("pk"),
        term__end_date__gt=timezone.now()
    )

    # Annotate each department with a boolean flag that indicates
    # if there's at least one course with an associated course instance
    # with a future term end_date (end_date > now)
    validated_departments = departments.annotate(
        has_future_course_instance=Exists(future_course_instance_exists)
    )

    return validated_departments

def _get_coursegroups_with_ci_future_end_date(course_groups: QuerySet[CourseGroup]) -> QuerySet[CourseGroup]:
    """
    Returns a QuerySet of CourseGroups that have at least one Course with a CourseInstance with a Term end_date
    in the future.
    """
    future_course_instance_exists = CourseInstance.objects.filter(
        course__course_group=OuterRef("pk"),
        term__end_date__gt=timezone.now()
    )

    # Annotate each department with a boolean flag that indicates
    # if there's at least one course with an associated course instance
    # with a future term end_date (end_date > now)
    validated_coursegroups = course_groups.annotate(
        has_future_course_instance=Exists(future_course_instance_exists)
    )

    return validated_coursegroups

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
