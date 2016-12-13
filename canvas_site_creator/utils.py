import logging
import json

from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from canvas_sdk.utils import get_all_list_data
from canvas_sdk.methods import courses as canvas_api_courses

from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.canvas_api.helpers import accounts as canvas_api_accounts_helper
from icommons_common.models import Term

from canvas_course_site_wizard.models import CanvasSchoolTemplate


logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)
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

def get_department_data_for_school(school_sis_account_id, department_sis_account_id=None):
    """
    get sub accounts where sis_account_id starts with dept
    :param school_sis_account_id:
    :param department_sis_account_id:
    :return:
    """
    departments = []
    school_sis_account_id = 'sis_account_id:{}'.format(school_sis_account_id)
    accounts = canvas_api_accounts_helper.get_all_sub_accounts_of_account(
        school_sis_account_id)
    for account in accounts:
        account_id = account['sis_account_id']
        if account_id and account_id.lower().startswith('dept:'):
            department = {
                'id': account_id.lower(),
                'name': account['name']
            }
            if department_sis_account_id and department_sis_account_id == account_id:
                return department
            else:
                departments.append(department)
    return departments


def get_course_group_data_for_school(school_sis_account_id, course_group_sis_account_id=None):
    """
    get sub accounts where sis_account_id starts with coursegroup
    :param school_sis_account_id:
    :param course_group_sis_account_id:
    :return:
    """
    course_groups = []
    school_sis_account_id = 'sis_account_id:{}'.format(school_sis_account_id)
    accounts = canvas_api_accounts_helper.get_all_sub_accounts_of_account(
        school_sis_account_id)
    for account in accounts:
        account_id = account['sis_account_id']
        if account_id and account_id.lower().startswith('coursegroup:'):
            course_group = {
                'id': account_id.lower(),
                'name': account['name']
            }
            if course_group_sis_account_id and course_group_sis_account_id == account_id:
                return course_group
            else:
                course_groups.append(course_group)
    return course_groups

def get_canvas_site_templates_for_school(school_id):
    """
    Get the Canvas site templates for the given school. First check the cache, if not found construct
    the Canvas site template dictionairy list by querying CanvasSchoolTemplate and the courses Canvas API
    to get the Canvas template site name.

    :param school_id:
    :return: List of dicts containing data for Canvas site templates for the given school
    """
    cache_key = CACHE_KEY_CANVAS_SITE_TEMPLATES_BY_SCHOOL_ID % school_id
    templates = cache.get(cache_key)
    if templates is None:
        templates = []
        for t in CanvasSchoolTemplate.objects.filter(school_id=school_id):
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
