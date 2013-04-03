from django.core.urlresolvers import reverse, reverse_lazy
from django.template import Context, loader
from django.template.response import TemplateResponse

from django.http import HttpResponse
from django.views import generic
from django.shortcuts import redirect
from django.contrib import messages
#from django.contrib.auth import authenticate, logout, login
#rom django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.http import urlquote

from icommons_common.models import *
from term_tool.forms import EditTermForm, CreateTermForm

import logging


logger = logging.getLogger(__name__)

### Mixins:

class TermActionMixin(object):
    def form_valid(self, form):
        msg = 'Term {0}!'.format(self.action)
        messages.success(self.request, msg)
        return super(TermActionMixin, self).form_valid(form)

class PinLoginRequiredMixin(object):
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)
### /Mixins


### Class-based views:

class SchoolListView(generic.ListView):
    model = School
    template_name = 'term_tool/school_list.html'
    context_object_name = 'school_list'

class TermListView(generic.ListView):
    """
    This view provides a list of all of the terms for a particular school.
    The school_id appears in the URL, and is available in the 'school_id' kwarg.
    The term list is paginated at 12 records per page.
    """
    model = Term
    template_name = 'term_tool/term_list.html'
    context_object_name = 'term_list'
    paginate_by = 12
    login_url = reverse_lazy('tt:login')
    
    # override the get_queryset method to limit the results to a particular school
    def get_queryset(self):
        return Term.objects.filter(school_id=self.kwargs['school_id']).order_by('-academic_year','term_code')
    
    # override the get_context_data method in order to add the 'school' object to the template context
    def get_context_data(self, **kwargs):
        context = super(TermListView, self).get_context_data(**kwargs)
        context['school'] = School.objects.get(pk=self.kwargs['school_id'])
        return context
    
class TermEditView(TermActionMixin, generic.edit.UpdateView):
    form_class = EditTermForm
    template_name = 'term_tool/term_edit.html'
    action = 'updated'
    model = Term
    context_object_name = 'term'
    login_url = reverse_lazy('tt:login')
        
    # override the get_success_url so that we can dynamically determine the URL to which the user should be redirected
    def get_success_url(self):
        return reverse('tt:termlist', kwargs={'school_id':self.object.school_id})

class TermCreateView(TermActionMixin, generic.edit.CreateView):
    form_class = CreateTermForm
    template_name = 'term_tool/term_create.html'
    action = 'created'
    model = Term
    login_url = reverse_lazy('tt:login')
    
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
        return context
    
    # override the get_success_url so that we can dynamically determine the URL to which the user should be redirected
    def get_success_url(self):
        return reverse('tt:termlist', kwargs={'school_id':self.object.school_id})
            
        