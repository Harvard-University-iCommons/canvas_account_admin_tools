import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from django_datatables_view.base_datatable_view import BaseDatatableView
from canvas_sdk.methods import (courses)
from canvas_sdk.exceptions import CanvasAPIError

from icommons_common.auth.views import LoginRequiredMixin
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import (School, CourseInstance)
from icommons_common.models import Term

from term_tool.forms import (CreateTermForm, EditTermForm)
from util import util


logger = logging.getLogger(__name__)

SDK_CONTEXT = SessionInactivityExpirationRC(**settings.CANVAS_SDK_SETTINGS)

### Mixins:

class TermActionMixin(object):
    def form_valid(self, form):
        logger.debug("form_valid called")
        msg = 'Term {0}!'.format(self.action)
        messages.success(self.request, msg)
        return super(TermActionMixin, self).form_valid(form)

### /Mixins


### Class-based views:

class SchoolListView(LoginRequiredMixin, generic.ListView):
    model = School
    template_name = 'term_tool/school_list.html'
    context_object_name = 'school_list'
    queryset = School.objects.filter(active=1)


class TermListView(LoginRequiredMixin, generic.ListView):
    """
    This view provides a list of all of the terms for a particular school.
    The school_id appears in the URL, and is available in the 'school_id' kwarg.
    The term list is paginated at 12 records per page.
    """
    model = Term
    template_name = 'term_tool/term_list.html'
    context_object_name = 'term_list'
    paginate_by = 12

    # override the get_queryset method to limit the results to a particular school
    def get_queryset(self):
        return Term.objects.filter(school_id=self.kwargs['school_id']).order_by('-academic_year', 'term_code')

    # override the get_context_data method in order to add the 'school' object to the template context
    def get_context_data(self, **kwargs):
        context = super(TermListView, self).get_context_data(**kwargs)
        school = School.objects.get(pk=self.kwargs['school_id'])
        context['school'] = school

        '''
        get the admin group from the settings object
        '''
        admingroup_str = settings.TERM_TOOL.get('ADMIN_GROUP', None)
        admingroup_set = set([admingroup_str])

        '''
        get the usergroups_set from the session
        '''
        logger.debug("USER_GROUPS from the session: " + ','.join(self.request.session['USER_GROUPS']) )
        usergroups_set = set(self.request.session['USER_GROUPS'])
        user_admin_set = admingroup_set & usergroups_set

        '''
        if a user is in the admin group, they can edit all terms for all schools.
        if not, they must be in the admin group for the specific school.
        '''
        if not user_admin_set:
            logger.debug('user is not a termtool global admin; checking the school group')
            '''
            get the allowed groups dict from the settings object
            '''
            allowedgroups_dict = settings.TERM_TOOL.get('ALLOWED_GROUPS', None)

            '''
            create a new set of just the keys from the allowed groups (key are group_id's)
            '''
            allowedgroups_set = set(allowedgroups_dict.keys())

            '''
            Get the intersection of the allowed groups and the users groups
            '''
            userauthgroups_set = allowedgroups_set & usergroups_set
            '''
            use the group id values from the intersection set userauthgroupids_set and build a new set
            of the names of the schools that the user has the authority to edit and create the AUTHORIZEDTOEDIT var
            in the context. This will be available in the template now.
            '''
            #authgroups_set = Set([])
            for group_id in userauthgroups_set:
                #authgroups_set.add(allowedgroups_dict[group_id])
                if allowedgroups_dict[group_id] == school.school_id:
                    context['AUTHORIZEDTOEDIT'] = True
        else:
            context['AUTHORIZEDTOEDIT'] = True

        return context


class TermEditView(LoginRequiredMixin, TermActionMixin, generic.edit.UpdateView):
    form_class = EditTermForm
    template_name = 'term_tool/term_edit.html'
    action = 'updated'
    model = Term
    context_object_name = 'term'

    def get_context_data(self, **kwargs):
        context = super(TermEditView, self).get_context_data(**kwargs)

        '''
        encrypt user_id to place in hidden field on form
        '''
        user_id = self.request.user.username
        encrypted_user = util.encrypt_string(user_id)
        context['USERID'] = encrypted_user

        logger.info('User %s opened TermEditView' % self.request.user)
        return context

    # override the get_success_url so that we can dynamically determine the URL to which the user should be redirected
    def get_success_url(self):
        logger.debug(self)
        logger.info('User %s edited term %s (%s %s)' % (self.request.user, self.object.term_id, self.object.school_id, self.object.display_name))
        return reverse('tt:termlist', kwargs={'school_id': self.object.school_id})


class TermCreateView(LoginRequiredMixin, TermActionMixin, generic.edit.CreateView):
    form_class = CreateTermForm
    template_name = 'term_tool/term_create.html'
    action = 'created'
    model = Term

    # override the get_initial method so that we can set the school based on the school_id that appears in the URL
    def get_initial(self):
        initial = super(TermCreateView, self).get_initial()
        #from pudb import set_trace; set_trace()
        initial['school'] = self.kwargs['school_id']
        return initial

    # override the get_context_data method in order to add the 'school' object to the template context
    def get_context_data(self, **kwargs):
        context = super(TermCreateView, self).get_context_data(**kwargs)
        context['school'] = School.objects.get(pk=self.kwargs['school_id'])
        #context['USERID'] = self.request.user
        user_id = self.request.user.username
        encrypted_user = util.encrypt_string(user_id)
        context['USERID'] = encrypted_user
        logger.info('User %s opened TermCreateView' % self.request.user)
        return context

    # override the get_success_url so that we can dynamically determine the URL to which the user should be redirected
    def get_success_url(self):
        logger.info('User %s created new term %s (%s %s)' % (self.request.user, self.object.term_id, self.object.school_id, self.object.display_name))
        return reverse('tt:termlist', kwargs={'school_id': self.object.school_id})


@login_required
def exclude_courses(request, term_id, school_id):
    return render(request, 'term_tool/exclude_courses.html',
                  {'term_id': term_id, 'school_id': school_id})


class ExcludeCoursesFromViewing(LoginRequiredMixin, BaseDatatableView):
    model = CourseInstance
    columns = ['course_instance_id', 'short_title', 'title', 'exclude_from_shopping']
    order_columns = columns
    max_display_length = 100

    def get_initial_queryset(self):
        term_id = self.kwargs['term_id']
        return self.model.objects.filter(sync_to_canvas=True, term_id=term_id).all()

    def post(self, request, *args, **kwargs):
        """
        Process AJAX requests from the exclude_courses.html template.
        We get params from the template then attempt to update the CourseInstance model
        and call the Canvas SDK to update the Canvas Course
        """
        user_id = self.request.user.username
        state = self.request.POST.get('state')
        course_instance_id = self.request.POST.get('course_instance_id')

        """
        TLT-1298:  Set the 'course_is_public_to_auth_users' to be the converse of 'state'. If the 'Disable auth user access'
        checkbox is checked, then set the course_is_public_to_auth_users flag being sent to Canvas to false and vice versa.
        """
        if state == 'true':
            exclude_from_shopping = True
            course_is_public_to_auth_users = 'false'
        else:
            exclude_from_shopping = False
            course_is_public_to_auth_users = 'true'

        """
        make sure we have all the params
        """
        if not (state and course_instance_id):
            return HttpResponse(json.dumps({'error': 'There was a problem updating the course.'}),
                                content_type="application/json", status=500)

        course_id = 'sis_course_id:%s' % course_instance_id
        """
        save the value to the database and log the transaction, if an error occurs log it and return an error response
        """
        try:
            course = CourseInstance.objects.get(course_instance_id=course_instance_id)
            course.exclude_from_shopping = exclude_from_shopping
            course.save()
            logger.info('user %s set course_is_public_to_auth_users on course %s to %s' % (user_id, course_instance_id, exclude_from_shopping))
        except CourseInstance.DoesNotExist:
            logger.exception('Error getting course_instance_id %s' % course_instance_id)
            return HttpResponse(json.dumps({'error': 'There was a problem updating course %s.' % course_instance_id}),
                                content_type="application/json", status=500)

        try:
            resp = courses.update_course(SDK_CONTEXT, course_id,
                                         course_is_public_to_auth_users=course_is_public_to_auth_users).json()
            logger.debug('update_course() response: %s' % json.dumps(resp, indent=2, sort_keys=True))

        except CanvasAPIError:
            logger.exception("CanvasAPIError in update_course() for course_id=%s with state=%s" % (course_id, state))
            return HttpResponse(json.dumps({'error': 'There was a problem updating course %s.' % course_instance_id}),
                                content_type="application/json", status=500)

        json_data = json.dumps({'success': 'Course %s has been updated!' % course_instance_id})
        logger.debug(json_data)
        return HttpResponse(json_data, content_type="application/json")
