import logging
from datetime import datetime
from django.utils import timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from django_auth_lti import const
from django_auth_lti.decorators import lti_role_required
from icommons_common.models import XlistMap, CsXlistMapOverview
from lti_permissions.decorators import lti_permission_required
from utils import create_crosslisting_pair, remove_cross_listing

logger = logging.getLogger(__name__)


@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def index(request):
    today = datetime.now()
    # The school that this tool is being launched in
    tool_launch_school = request.LTI['custom_canvas_account_sis_id'].split(':')[1]

    # Only get cross listings with current or future terms
    # Either the primary or secondary courses must be from the school launching the tool
    xlist_maps = XlistMap.objects.filter(Q(primary_course_instance__term__end_date__gte=today) |
                                         Q(secondary_course_instance__term__end_date__gte=today) |
                                         Q(primary_course_instance__term__end_date__isnull=True) |
                                         Q(secondary_course_instance__term__end_date__isnull=True)).filter(
                                         Q(primary_course_instance__course__school=tool_launch_school) |
                                         Q(secondary_course_instance__course__school=tool_launch_school)).select_related('primary_course_instance',
                                                                                                                        'secondary_course_instance')



    context = {
        'xlist_maps': xlist_maps,
    }
    return render(request, 'list.html', context=context)

@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def add_new_pair(request):
    # get the school id
    sis_account_id = request.LTI['custom_canvas_account_sis_id']
    school_id = sis_account_id.split(':')[1]
    today = datetime.now()

    # todo filter those entries that are already cross listed and are present in XLIST tables.
    #  Possibly add a column in the view to do so

    potential_mappings = CsXlistMapOverview.objects.filter(Q(primary_school_id=school_id)).filter(
        Q(term_end_date__gte=today) | Q(term_end_date__isnull=True)).filter(
        Q(existing_mapping__isnull=True)).filter(
        Q(existing_reverse_mapping__isnull=True))

    context = {
        'potential_mappings': potential_mappings,
        'school_id': school_id,
    }

    return render(request, 'add_new.html', context=context)

@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET', 'POST'])
def create_new_pair(request):

    if request.method == 'POST':
        primary_id = request.POST['primary_course_input']
        secondary_id = request.POST['secondary_course_input']
        create_crosslisting_pair(primary_id, secondary_id,request)

    else:
        primary_id = request.GET.get("primary_course_input", None)
        secondary_id = request.GET.get("secondary_course_input", None)
        create_crosslisting_pair(primary_id, secondary_id,request)

    return redirect('cross_list_courses:add_new_pair')

@login_required
@lti_role_required(const.ADMINISTRATOR)
@lti_permission_required(settings.PERMISSION_XLIST_TOOL)
@require_http_methods(['GET'])
def delete_cross_listing(request, pk):
    remove_cross_listing(pk, request)
    return redirect('cross_list_courses:index')
