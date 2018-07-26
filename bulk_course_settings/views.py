import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.edit import FormView, CreateView

from bulk_course_settings.forms import (CreateBulkSettingsForm)
from bulk_course_settings.models import BulkCourseSettingsJob
from bulk_course_settings.utils import queue_bulk_settings_job
from icommons_common.auth.views import (LoginRequiredMixin)
from .utils import get_term_data_for_school

logger = logging.getLogger(__name__)
JOB_QUEUE_NAME = settings.BULK_COURSE_SETTINGS['job_queue_name']


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


class BulkSettingsCreateView(LoginRequiredMixin, CreateView, FormView):

    form_class = CreateBulkSettingsForm
    template_name = 'bulk_course_settings/create_new_setting.html'
    context_object_name = 'create_new_setting'
    model = BulkCourseSettingsJob

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsCreateView, self).get_context_data(**kwargs)
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        context['account_sis_id'] = account_sis_id
        context['terms'] = get_term_data_for_school(account_sis_id)
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super(BulkSettingsCreateView, self).form_valid(form)


class BulkSettingsRevertView(LoginRequiredMixin, generic.edit.CreateView):
    form_class = ""


def add_bulk_job(request):

    # invoke method to add to sqs
    queryset = BulkCourseSettingsJob.objects.all()
    for job in queryset:
        logger.debug(
            "job.school_id=%s, job.setting_to_be_modifiedd=%s "
            % (job.school_id, job.setting_to_be_modified))
        print job.school_id+",job.setting_to_be_modified="+job.setting_to_be_modified

        queue_bulk_settings_job(JOB_QUEUE_NAME, job.id, job.school_id, job.term_id,
                                job.setting_to_be_modified)

    return HttpResponseRedirect(reverse('bulk_course_settings:bulk_settings_list'))

