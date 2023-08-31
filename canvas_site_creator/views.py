import logging

from coursemanager.models import (Course, CourseInstance,
                                  School)
from django.conf import settings
from django.contrib import messages
from django.db.utils import IntegrityError

from common.utils import (get_department_data_for_school,
                          get_term_data_for_school)

from .utils import create_canvas_course_and_section
import logging

from canvas_api.helpers import accounts as canvas_api_accounts
from coursemanager.models import CourseGroup, Department, School, Term
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from lti_school_permissions.decorators import lti_permission_required

from common.utils import (get_canvas_site_templates_for_school,
                    get_course_group_data_for_school,
                    get_department_data_for_school, get_term_data_for_school)

logger = logging.getLogger(__name__)


@login_required
@lti_permission_required(canvas_api_accounts.ACCOUNT_PERMISSION_MANAGE_COURSES)
@require_http_methods(['GET', 'POST'])
def create_new_course(request):
    # Depending on the type of request (POST vs GET), these values may not be set.
    # If they are not set, we will use the default values below.
    selected_course_group_data = None
    selected_department_id = None

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

    course_groups = None
    departments = None
    if school_id == 'colgsas':
        try:
            course_groups = get_course_group_data_for_school(sis_account_id)
        except Exception:
            logger.exception(f"Failed to get course groups with sis_account_id {sis_account_id}")
    else:
        try:
            departments = get_department_data_for_school(sis_account_id)
        except Exception:
            logger.exception(f"Failed to get departments with sis_account_id {sis_account_id}")

    if request.method == 'POST':
        # On POST, create new Course and CourseInstance records and then the course in Canvas
        post_data = request.POST.dict()

        is_blueprint = True if post_data.get('is_blueprint') else False
        selected_course_group_data = post_data.get("courseCourseGroup", None)
        selected_department_id = post_data.get("courseDepartment", None)
        term = Term.objects.get(term_id=post_data['course-term'])
        course_code_type = post_data["course-code-type"]
        template_id = post_data['template-select'] if post_data['template-select'] != 'No template' else None

        department = None
        course_group = None
        if selected_department_id:
            department = Department.objects.get(department_id=selected_department_id)
        else:
            # If the course group is "Informal Learning Experiences" or "Sandbox Courses", we need
            # to search against the Department schema as ILE/SB sub-accounts are designated
            # as departments.
            course_group_id, name = selected_course_group_data.split(' ', 1)
            if name.lower() == 'informal learning experiences' or name.lower() == 'sandbox courses':
                department = Department.objects.get(department_id=course_group_id)
            else:
                course_group = CourseGroup.objects.get(course_group_id=course_group_id)

        logger.info(f'Creating Course and CourseInstance records from the posted site creator info.', extra=post_data)

        try:
            course = Course.objects.create(
                registrar_code=f'{course_code_type}-{post_data["course-code"]}',
                registrar_code_display=f'{course_code_type}-{post_data["course-code"]}',
                school=school,
                department=department,
                course_group=course_group,
            )
        except IntegrityError:
            logger.error(f'The course code already exists. '
                         f'Could not create Course and CourseInstance records '
                         f'from the posted site creator info.', extra=post_data)
            messages.add_message(request,
                                 messages.ERROR,
                                 'The course could not successfully be created. '
                                 'The course code already exists.')
            return redirect('canvas_site_creator:create_new_course')

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
                                 f'Course <a href="{ settings.CANVAS_URL }/courses/{ course_instance.canvas_course_id }" target="_blank">{ course_instance.canvas_course_id }</a> successfully created.')
        else:
            messages.add_message(request,
                                 messages.ERROR,
                                 'The course could not successfully be created. '
                                 'Please try again or contact support if the issue persists.')

        return redirect('canvas_site_creator:create_new_course')

    context = {
        'school_id': school_id,
        'school_name': school.title_short,
        'canvas_site_templates': canvas_site_templates,
        'terms': terms,
        'canvas_url': settings.CANVAS_URL,
        'departments': departments,
        'course_groups': course_groups,
    }

    return render(request, 'canvas_site_creator/index.html', context)
