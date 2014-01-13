from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages

#from django.views.decorators.http import require_http_methods

#from ims_lti_py.tool_provider import DjangoToolProvider
from icommons_common.auth.views import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from icommons_common.models import School, CourseInstance
from icommons_common.canvas_utils import *
from django.core.cache import cache
from django.views import generic
from django.conf import settings


import logging
from django.views.decorators.csrf import csrf_exempt

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from collections import defaultdict


logger = logging.getLogger(__name__)

# Create your views here.

'''
The course view checks to see if the authenticated user is already enrolled in the course.
If not, and if shopping period is still active for the course, then the user will be
enrolled in the course as a shopper.
'''


@login_required
def course(request, canvas_course_id):

    course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)

    # is the user already in the course?
    user_id = request.user.username
    is_enrolled = False
    enrollments = get_canvas_enrollment_by_user('sis_user_id:%s' % user_id)
    if enrollments:
        for e in enrollments:
            logger.debug('user %s is enrolled in %d - checking against %s' % (user_id, e['course_id'], canvas_course_id))
            if e['course_id'] == int(canvas_course_id):
                is_enrolled = True
                break

    if is_enrolled is True:
        # redirect the user to the actual canvas course site
        course_url = '%s/courses/%s' % (settings.CANVAS_SHOPPING['CANVAS_BASE_URL'], canvas_course_id)
        logger.info('User %s is already enrolled in course %s - redirecting to site.' % (user_id, canvas_course_id))
        return redirect(course_url)

    else:
        canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)

        # make sure this is a shoppable course
        is_shoppable = False
        course_instance_id = None
        course_instances = CourseInstance.objects.filter(canvas_course_id=canvas_course_id)
        for ci in course_instances:
            if ci.term.shopping_active:
                is_shoppable = True
                course_instance_id = ci.course_instance_id
                break

        if is_shoppable is False:
            return render(request, 'canvas_shopping/not_shoppable.html', {'canvas_course': canvas_course})

        else:
            # Enroll this user as a shopper
            #new_enrollee = add_canvas_course_enrollee(canvas_course_id, 'Shopper', user_id)
            new_enrollee = add_canvas_section_enrollee('sis_section_id:%d' % course_instance_id, 'Shopper', user_id)
            if new_enrollee:
                # success
                return render(request, 'canvas_shopping/successfully_added.html', {'canvas_course': canvas_course, 'course_url': course_url})

            else:
                return render(request, 'canvas_shopping/error_adding.html', {'canvas_course': canvas_course})


@api_view(['GET'])
@authentication_classes([TokenAuthentication, SessionAuthentication, ])
@permission_classes([IsAuthenticated, ])
def index(request):
    authenticator = request.successful_authenticator.__class__.__name__
    #from pudb import set_trace; set_trace()
    return Response({'authenticator': authenticator, })


class SchoolListView(LoginRequiredMixin, generic.ListView):
    model = School
    template_name = 'canvas_shopping/school_list.html'
    context_object_name = 'school_list'
    queryset = School.objects.filter(active=1, courses__course_instances__sync_to_canvas=1).distinct()


class CourseListView(LoginRequiredMixin, generic.ListView):
    model = CourseInstance
    template_name = 'canvas_shopping/course_list.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CourseListView, self).get_context_data(**kwargs)
        courses = {}
        enrollments = {}

        # Get the list of courses that this user is already shopping (in Canvas)
        enrollees = get_enrollments_by_user(self.request.user.username, 'Shopper')
        if enrollees is not None:
            for e in enrollees:
                canvas_course_id = e['course_id']
                canvas_course = get_canvas_course_by_canvas_id(canvas_course_id)
                if canvas_course:
                    if canvas_course['sis_course_id']:
                        #shopped_course_instance_ids[ int(canvas_course['sis_course_id']) ] = canvas_course_id
                        logger.debug('user %s is enrolled in canvas/harvard course %d/%s' % ( self.request.user.username, canvas_course_id, canvas_course['sis_course_id']))
                        enrollments[int(canvas_course['sis_course_id'])] = e

        # Get the Canvas courses for this school
        course_instances = CourseInstance.objects.filter(course__school__school_id=self.kwargs['school_id'], sync_to_canvas=1)
        for ci in course_instances:
            courses[ci.course_instance_id] = {'instance': ci, 'enrollee': enrollments.get(ci.course_instance_id)}


        # Add in a QuerySet of all the courses
        context['course_list'] = courses
        context['school'] = School.objects.get(pk=self.kwargs['school_id'])
        #context['enrollments'] = enrollments
        #context['shopped_course_instance_ids'] = shopped_course_instance_ids
        context['canvas_base_url'] = settings.CANVAS_SHOPPING['CANVAS_BASE_URL']
        return context

# need a view for HDS students: display the list of Canvas-mapped courses for HDS + active shopping terms


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, ])
@permission_classes([IsAuthenticated, ])
@csrf_exempt
def add_shopper(request):

    # request must contain user_id, school, academic_year, term_code, course_code

    # first, check the school/course_code/year/term to see if it's a canvas course - if not, return immediately
    school_id = request.DATA['school_id']
    course_code = request.DATA['course_code']
    academic_year = request.DATA['academic_year']
    term_code = request.DATA['term_code']

    if school_id and course_code and academic_year and term_code:
        # look up the course - is it using canvas?
        course_key = '%s-%s-%s-%s' % (school_id, course_code, academic_year, term_code)
        canvas_course_info = get_canvas_info(course_key)

        if canvas_course_info is not None and canvas_course_info.get('course_instance_id') is not None:
            # if the authentication method is SessionAuthentication, get the user_id from the authenticated user object
            if request.successful_authenticator.__class__.__name__ == 'SessionAuthentication':
                user_id = request.user.user_id
            else:
                user_id = request.DATA['shopper_id']

            section = get_canvas_course_section(canvas_course_info.get('course_instance_id'))

            if section is not None:
                enrollee = add_canvas_section_enrollee(section['id'], 'Shopper', user_id)
                if enrollee is not None:
                    return Response({'status': 'success'})
                else:
                    return Response({'status': 'error', 'message': 'Could not add user to course. Please try again later.'})
            else:
                return Response({'status': 'error', 'message': 'Could not find the Canvas section.'})

        else:
            return Response({'status': 'success', 'message': 'Not a Canvas course.'})

    else:
        return Response({'status': 'error', 'messge': 'One of the required parameters is missing.'})


@login_required
def add_shopper_ui(request):

    # request must contain user_id, school, academic_year, term_code, course_code

    # first, check the school/course_code/year/term to see if it's a canvas course - if not, return immediately
    user_id = request.user.username
    course_instance_id = request.POST.get('course_instance_id')
    school_id = request.POST.get('school_id')
    #from pudb import set_trace; set_trace()
    if course_instance_id:
        ci = CourseInstance.objects.get(pk=course_instance_id)
        section = get_canvas_course_section(ci.course_instance_id)
        if section is not None:
            enrollee = add_canvas_section_enrollee(section['id'], 'Shopper', user_id)
            if enrollee is not None:
                messages.success(request, 'Successfully updated your shopping list.')
            else:
                messages.error(request, 'Could not update your shopping list. Please try again later')

        else:
            messages.error(request, 'There was a problem with the Canvas course.')

    else:
        messages.error(request, 'No course ID was sent.')

    next_url = reverse('sh:courselist', args=[school_id])
    return redirect(next_url)


@login_required
def remove_shopper_ui(request):
    canvas_course_id = request.POST.get('canvas_course_id')
    canvas_enrollee_id = request.POST.get('canvas_enrollee_id')
    school_id = request.POST.get('school_id')

    if canvas_course_id and canvas_enrollee_id:
        delete_canvas_enrollee_id(int(canvas_course_id), int(canvas_enrollee_id))
        messages.success(request, 'Successfully updated your shopping list.')
    else:
        messages.error(request, 'Could not update your shopping list. Please try again later')
    next_url = reverse('sh:courselist', args=[school_id])
    return redirect(next_url)


@api_view(['POST'])
@authentication_classes([TokenAuthentication, SessionAuthentication, ])
@permission_classes([IsAuthenticated, ])
@csrf_exempt
def remove_shopper(request):

    # request must contain user_id, school, academic_year, term_code, course_code

    # first, check the school/course_code/year/term to see if it's a canvas course - if not, return immediately
    school_id = request.DATA['school_id']
    course_code = request.DATA['course_code']
    academic_year = request.DATA['academic_year']
    term_code = request.DATA['term_code']

    if school_id and course_code and academic_year and term_code:
        # look up the course - is it using canvas?
        course_key = '%s-%s-%s-%s' % (school_id, course_code, academic_year, term_code)
        canvas_course_info = get_canvas_info(course_key)

        if canvas_course_info is not None and canvas_course_info.get('canvas_course_id') is not None:
            # if the authentication method is SessionAuthentication, get the user_id from the authenticated user object
            if request.successful_authenticator.__class__.__name__ == 'SessionAuthentication':
                user_id = request.user.user_id
            else:
                user_id = request.DATA['shopper_id']

            # fetch the canvas enrollee ID
            canvas_enrollee_id = None
            enrollees = get_enrollments_by_user(user_id, 'Shopper')
            for e in enrollees:
                if e['course_id'] == canvas_course_info.get('canvas_course_id'):
                    canvas_enrollee_id = e['id']
                    break

            if canvas_enrollee_id is not None:
                # remove the enrollee
                delete_canvas_enrollee_id(canvas_course_info.get('canvas_course_id'), int(canvas_enrollee_id))
                return Response({'status': 'success'})
            else:
                return Response({'status': 'error', 'message': 'Could not remove user from course. Please try again later.'})
        else:
            return Response({'status': 'success', 'message': 'Not a Canvas course.'})
    else:
        return Response({'status': 'error', 'messge': 'One of the required parameters is missing.'})


def get_canvas_courses():
    # get/store canvas course map from cache
    course_map = cache.get('canvas_course_map')
    logger.debug('canvas course cache: %s' % course_map)
    if course_map is None:
        logger.debug('canvas course cache was empty - will set')
        course_map = {}
        # fetch from the database
        canvas_courses = CourseInstance.objects.filter(sync_to_canvas=1)
        for c in canvas_courses:
            course_key = '%s-%s-%d-%d' % (c.course.school.school_id, c.course.registrar_code, c.term.academic_year, c.term.term_code.term_code)
            course_map[course_key] = {'course_instance_id': c.course_instance_id, 'canvas_course_id': c.canvas_course_id}
            logger.debug('caching %s' % course_key)

        cache.set('canvas_course_map', course_map)
    else:
        logger.debug('found canvas course cache')
    return course_map


def get_canvas_info(course_key):
    logger.debug('looking for canvas course with key %s' % course_key)
    course_map = get_canvas_courses()
    if course_key in course_map:
        return course_map[course_key]
    else:
        return None


# helper to build nested dicts:
def tree():
    return defaultdict(tree)
