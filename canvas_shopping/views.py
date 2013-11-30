from django.shortcuts import render
#from django.views.decorators.http import require_http_methods

#from ims_lti_py.tool_provider import DjangoToolProvider
from icommons_common.auth.views import LoginRequiredMixin
from icommons_common.models import School, CourseInstance
from icommons_common.canvas_utils import *
from django.views import generic

import logging

logger = logging.getLogger(__name__)

# Create your views here.


def index(request):

    return render(request, 'canvas_shopping/index.html')

class SchoolListView(LoginRequiredMixin, generic.ListView):
    model = School
    template_name = 'canvas_shopping/school_list.html'
    context_object_name = 'school_list'
    queryset = School.objects.filter(active=1, courses__course_instances__sync_to_canvas=1)


class CourseListView(LoginRequiredMixin, generic.ListView):
    model = CourseInstance
    template_name = 'canvas_shopping/course_list.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CourseListView, self).get_context_data(**kwargs)

        # Get the list of courses that this user is already shopping (in Canvas)
        shopped_course_instance_ids = []
        enrollments = get_enrollments_by_user(self.request.user.username, 'Shopper')
        for e in enrollments:
            canvas_course_id = e['course_id']
            canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)
            if canvas_course:
                if canvas_course['sis_course_id']:
                    shopped_course_instance_ids.append(int( canvas_course['sis_course_id']))

        # Add in a QuerySet of all the courses
        context['course_list'] = CourseInstance.objects.filter(course__school__school_id=self.kwargs['school_id'], sync_to_canvas=1)
        context['school'] = School.objects.get(pk=self.kwargs['school_id'])
        context['enrollments'] = enrollments
        context['shopped_course_instance_ids'] = shopped_course_instance_ids
        return context


# need a view for HDS students: display the list of Canvas-mapped courses for HDS + active shopping terms

def add_shopper(request):

    # request must contain user_id, school, academic_year, term_code, course_code

    return "some json result"

def remove_shopper(request): 

    # request must contain user_id, school, academic_year, term_code, course_code

    return "some json result"