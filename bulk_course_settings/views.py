import logging

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormView, CreateView
from django.views import View

from bulk_course_settings import constants
from bulk_course_settings import utils
from bulk_course_settings.forms import CreateBulkSettingsForm
from bulk_course_settings.models import BulkCourseSettingsJob, BulkCourseSettingsJobDetails
from icommons_common.auth.views import LoginRequiredMixin

logger = logging.getLogger(__name__)


def lti_auth_error(request):
    raise PermissionDenied


class BulkSettingsListView(LoginRequiredMixin, ListView):
    model = BulkCourseSettingsJob
    template_name = 'bulk_course_settings/bulk_settings_list.html'
    context_object_name = 'bulk_settings_list'
    queryset = BulkCourseSettingsJob.objects.all()


class BulkSettingsCreateView(LoginRequiredMixin, CreateView, FormView):

    form_class = CreateBulkSettingsForm
    template_name = 'bulk_course_settings/create_new_setting.html'
    context_object_name = 'create_new_setting'
    model = BulkCourseSettingsJob

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsCreateView, self).get_context_data(**kwargs)
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        context['account_sis_id'] = account_sis_id
        context['school_id'] = account_sis_id.split(':')[1]
        context['terms'] = utils.get_term_data_for_school(account_sis_id)
        return context

    def form_valid(self, form):
        # If the form is valid, create the BulkCourseSettingsJob and add it to the SQS queue
        form.instance.created_by = str(self.request.user)
        response = super(BulkSettingsCreateView, self).form_valid(form)

        utils.queue_bulk_settings_job(bulk_settings_id=form.instance.id, school_id=form.instance.school_id,
                                      term_id=form.instance.term_id,
                                      setting_to_be_modified=form.instance.setting_to_be_modified,
                                      desired_setting=form.instance.desired_setting)
        form.instance.workflow_status = constants.QUEUED
        form.instance.save()

        return response


class BulkSettingsRevertView(LoginRequiredMixin, View):

    def get(self, request, school_id, job_id):
        related_bulk_job = BulkCourseSettingsJob.objects.get(id=job_id)
        new_bulk_job = BulkCourseSettingsJob.objects.create(related_job_id=related_bulk_job.id,
                                                            school_id=school_id,
                                                            term_id=related_bulk_job.term_id,
                                                            setting_to_be_modified=related_bulk_job.setting_to_be_modified)

        utils.queue_bulk_settings_job(bulk_settings_id=new_bulk_job.id, school_id=school_id,
                                      term_id=related_bulk_job.term_id,
                                      setting_to_be_modified=related_bulk_job.setting_to_be_modified,
                                      desired_setting='REVERT')
        new_bulk_job.workflow_status = constants.QUEUED
        new_bulk_job.save()

        return redirect(reverse('bulk_course_settings:bulk_settings_list'))


class BulkSettingsAuditView(LoginRequiredMixin, ListView):
    model = BulkCourseSettingsJobDetails
    template_name = 'bulk_course_settings/bulk_settings_job_audit.html'
    context_object_name = 'job_details'

    def get_queryset(self):
        return BulkCourseSettingsJobDetails.objects.filter(parent_job_process_id=self.kwargs['parent_job_process_id'])

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsAuditView, self).get_context_data(**kwargs)
        context['parent_job'] = BulkCourseSettingsJob.objects.get(id=self.kwargs['parent_job_process_id'])
        return context
    # def get(self, request, parent_job_process_id):


