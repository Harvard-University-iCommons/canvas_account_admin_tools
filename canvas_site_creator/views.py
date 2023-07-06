import logging

from canvas_api.helpers import accounts as canvas_api_accounts
from common.utils import get_canvas_site_templates_for_school, get_term_data_for_school
from coursemanager.models import CourseInstance, Course, Department, Term
from coursemanager.models import School
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from lti_school_permissions.decorators import lti_permission_required

from .utils import create_canvas_course_and_section

logger = logging.getLogger(__name__)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET', 'POST'])
def create_new_course(request):
    sis_account_id = request.LTI['custom_canvas_account_sis_id']

    try:
        school_id = sis_account_id.split(':')[1]
        school = School.objects.get(school_id=school_id)
    except School.objects.DoesNotExist as e:
        logger.exception(f"School does not exist for given sis_account_id: {sis_account_id}")
        raise Exception
    if not school:
        return render(request, 'canvas_site_creator/restricted_access.html', status=403)

    canvas_site_templates = get_canvas_site_templates_for_school(school_id)
    terms, _current_term_id = get_term_data_for_school(sis_account_id)

    if request.method == 'POST':
        # On POST, create new Course and CourseInstance records and then the course in Canvas
        post_data = request.POST.dict()

        is_blueprint = True if post_data.get('is_blueprint') else False
        # Associate blueprint courses with the schools ILE department
        department_short_name = 'ILE' if post_data["course-code-type"] == 'BLU' else post_data["course-code-type"]
        department = Department.objects.get(school=school_id, short_name=department_short_name)
        term = Term.objects.get(term_id=post_data['course-term'])
        course_code_type = post_data["course-code-type"]
        template_id = post_data['templateSelect'] if post_data['templateSelect'] != 'No template' else None

        logger.info(f'Creating Course and CourseInstance records from the posted site creator info: {post_data}')

        course = Course.objects.create(
            registrar_code=f'{course_code_type}-{post_data["course-code"]}',
            registrar_code_display=f'{course_code_type}-{post_data["course-code"]}',
            school=school,
            department=department
        )

        course_instance = CourseInstance.objects.create(
            course=course,
            section='001',
            exclude_from_catalog=1,
            short_title=post_data['course-short-title'],
            title=post_data['course-title'],
            sync_to_canvas=0,
            term=term
        )

        course_data = {
            'sis_account_id': sis_account_id,
            'course': course,
            'course_instance': course_instance,
            'is_blueprint': is_blueprint,
            'template_id': template_id
        }

        canvas_course = create_canvas_course_and_section(course_data)

        if canvas_course:
            course_instance.sync_to_canvas = 1
            course_instance.canvas_course_id = canvas_course['id']
            course_instance.parent_course_instance = None
            course_instance.save()

            messages.add_message(request,
                                 messages.SUCCESS,
                                 course_instance.canvas_course_id)
        else:
            messages.add_message(request,
                                 messages.ERROR,
                                 'The course could not successfully be created. '
                                 'Please try again or contact support if the issue persists.')

        return redirect('canvas_site_creator:create_new_course')

    context = {'school_id': school_id,
               'school_name': school.title_short,
               'canvas_site_templates': canvas_site_templates,
               'terms': terms,
               'canvas_url': settings.CANVAS_URL}

    return render(request, 'canvas_site_creator/index.html', context)
