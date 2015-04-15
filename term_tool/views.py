import json
import logging

from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib import messages
from icommons_common.models import (School, CourseInstance)
from icommons_common.auth.views import LoginRequiredMixin
from django.http import HttpResponse
from django.conf import settings
from canvas_sdk.methods import (courses)
from canvas_sdk.exceptions import CanvasAPIError
from icommons_common.canvas_utils import SessionInactivityExpirationRC
from icommons_common.models import Term

from term_tool.forms import (EditTermForm, CreateTermForm,) # EditCourseInstanceForm)
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
        self.request.session['USER_GROUPS'].append('IcGroup:25095')
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


class ExcludeCoursesFromViewing(LoginRequiredMixin, TermActionMixin, generic.ListView):

    template_name = 'term_tool/exclude_courses.html'
    model = CourseInstance

    def get_queryset(self):
        term_id = self.kwargs['term_id']
        return CourseInstance.objects.filter(term=term_id, sync_to_canvas=True)

    def get_context_data(self, **kwargs):
        context = super(ExcludeCoursesFromViewing, self).get_context_data(**kwargs)
        """
        encrypt user_id to place in hidden field on form
        """
        user_id = self.request.user.username
        encrypted_user = util.encrypt_string(user_id)
        context['term_id'] = self.kwargs['term_id']
        context['school_id'] = self.kwargs['school_id']
        context['USERID'] = encrypted_user

        return context


    def post(self, request, *args, **kwargs):
        state = self.request.POST.get('state')
        school_id = self.request.POST.get('school_id')
        course_instance_id = self.request.POST.get('course_instance_id')
        if state == 'false':
            exclude_from_shopping = False
        else:
            exclude_from_shopping = True

        logger.debug('state: %s' % state)
        if state and school_id and course_instance_id:
            account_id = 'sis_account_id:'+school_id
            course_id = 'sis_course_id:'+course_instance_id
            """
            save the value to the database
            """
            try:
                course = CourseInstance.objects.get(course_instance_id=course_instance_id)
                course.exclude_from_shopping = exclude_from_shopping
                course.save()
            except ObectDoesNotExist as e:
                logger.exception(e)
                return HttpResponse(json.dumps({ 'Error': 'database error'}), content_type="application/json")

            try:
                resp = courses.update_course(SDK_CONTEXT, course_id, account_id, course_is_public_to_auth_users=state).json()
                logger.debug('id: %s, is_public_to_auth_users: %s' % (resp.get('id'), resp.get('is_public_to_auth_users')))

            except CanvasAPIError as api_error:
                logger.error("CanvasAPIError in update_course call for course_id=%s in sub_account=%s wityh state=%s. Exception=%s:"
                     % (course_id, account_id, state, api_error))
                return HttpResponse(json.dumps({ 'Error': 'canvas api error'}), content_type="application/json")
        else:
            return HttpResponse(json.dumps({ 'Error': 'missing parameters'}), content_type="application/json")

        json_data = json.dumps({ 'success': 'Course %s updated!' % course_instance_id})
        logger.debug(json_data)
        return HttpResponse(json_data, content_type="application/json")