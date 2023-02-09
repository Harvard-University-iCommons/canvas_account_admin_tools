import logging
from ast import literal_eval
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.canvas_utils import (SessionInactivityExpirationRC) # TODO replace this
from lti_permissions.decorators import lti_permission_required
from common.utils import (
    get_term_data_for_school,
    get_canvas_site_templates_for_school,
)
from icommons_common.models import School, CourseInstance

logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_BULK_SITE_CREATOR)
@require_http_methods(['GET', 'POST'])
def index(request):
    sis_account_id = request.LTI['custom_canvas_account_sis_id']
    terms, _current_term_id = get_term_data_for_school(sis_account_id)
    school_id = sis_account_id.split(':')[1]
    school = School.objects.get(school_id=school_id)
    canvas_site_templates = get_canvas_site_templates_for_school(school_id)
    potential_course_sites_query = None

    if request.method == 'POST':
        selected_term = request.POST['course-term']
        selected_template = request.POST['template-select']
        # Retrieve all course instances for the given term and account that do not have Canvas course sites
        # nor are set to be fed into Canvas via the automated feed
        potential_course_sites_query = get_course_instance_query_set(selected_term, sis_account_id).filter(
            canvas_course_id__isnull=True, sync_to_canvas=0)

    # TODO maybe better to use template tag unless used elsewhere?
    potential_course_site_count = potential_course_sites_query.count() if potential_course_sites_query else 0

    context = {
        'terms': terms,
        'potential_course_sites': potential_course_sites_query,
        'potential_site_count': potential_course_site_count,
        'canvas_site_templates': canvas_site_templates
     }
    return render(request, 'bulk_site_creator/index.html', context=context)


#  TODO Currently a method in canvas_site_creator models, using for temp testing
def get_course_instance_query_set(sis_term_id, sis_account_id):
    # Exclude records that have parent_course_instance_id  set(TLT-3558) as we don't want to create sites for the
    # children; they will be associated with the parent site
    filters = {'exclude_from_isites': 0, 'term_id': sis_term_id, 'parent_course_instance_id__isnull': True}

    logger.debug(f'Getting CI objects for term: {sis_term_id} and school: {sis_account_id}')

    (account_type, account_id) = sis_account_id.split(':')
    if account_type == 'school':
        filters['course__school'] = account_id
    elif account_type == 'dept':
        filters['course__department'] = account_id
    elif account_type == 'coursegroup':
        filters['course__course_group'] = account_id

    return CourseInstance.objects.filter(**filters)

