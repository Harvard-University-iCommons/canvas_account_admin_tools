import logging
import time

from django.conf import settings

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import HttpResponse
from django.views import generic
from django.views.generic.edit import CreateView
from icommons_common.auth.views import (LoginRequiredMixin)
from bulk_course_settings.models import BulkCourseSettingsJob, BulkCourseSettingsJobDetails
from bulk_course_settings.forms import (CreateBulkSettingsForm)
from icommons_common.models import Term, TermCode, School
from .utils import get_term_data_for_school

logger = logging.getLogger(__name__)

COURSE_INSTANCE_FILTERS = ['school', 'term', 'department', 'course_group']


def lti_auth_error(request):
    raise PermissionDenied


class BulkSettingsListView(LoginRequiredMixin, generic.ListView):
    model = BulkCourseSettingsJob
    template_name = 'bulk_course_settings/bulk_settings_list.html'
    context_object_name = 'bulk_settings_list'
    queryset = BulkCourseSettingsJob.objects.all()

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsListView, self).get_context_data(**kwargs)
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        context['account_sis_id'] = account_sis_id
        return context

class BulkSettingsCreateView(LoginRequiredMixin, generic.edit.CreateView):

    form_class = CreateBulkSettingsForm
    template_name = 'bulk_course_settings/create_new_setting.html'
    context_object_name = 'create_new_setting'
    # action = 'created'
    model = BulkCourseSettingsJob
    #terms, current_term_id = get_term_data_for_school(account_sis_id)

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsCreateView, self).get_context_data(**kwargs)
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        context['account_sis_id'] = account_sis_id
        context['terms'] = get_term_data_for_school(account_sis_id)
        return context

#class BulkSettingsTermView(LoginRequiredMixin, generic.ListView):
#    model = Term
#    template_name = 'bulk_course_settings/term_code.html'
#    context_object_name = 'term_code'
#    queryset = Term.objects.all()


