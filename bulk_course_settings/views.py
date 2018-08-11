import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from bulk_course_settings import constants
from bulk_course_settings import utils
from bulk_course_settings.forms import CreateBulkSettingsForm
from bulk_course_settings.models import Job
from icommons_common.auth.views import LoginRequiredMixin

logger = logging.getLogger(__name__)


def lti_auth_error(request):
    raise PermissionDenied


class BulkSettingsListView(LoginRequiredMixin, ListView):
    """Display a table with all Jobs created from this account."""
    model = Job
    template_name = 'bulk_course_settings/job_list.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        school_id = account_sis_id.split(':')[1]
        return Job.objects.filter(school_id=school_id)


class BulkSettingsCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Displays the form used to create a Job with the desired setting and value"""
    form_class = CreateBulkSettingsForm
    template_name = 'bulk_course_settings/create_new_job.html'
    model = Job
    success_message = "Job was created successfully"

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsCreateView, self).get_context_data(**kwargs)
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        context['account_sis_id'] = account_sis_id
        context['school_id'] = account_sis_id.split(':')[1]
        context['terms'] = utils.get_term_data_for_school(account_sis_id)
        return context

    def form_valid(self, form):
        """If the form is valid, create the Job and add it to the SQS queue"""
        form.instance.created_by = str(self.request.user)
        response = super(BulkSettingsCreateView, self).form_valid(form)

        utils.queue_bulk_settings_job(bulk_settings_id=form.instance.id, school_id=form.instance.school_id,
                                      term_id=form.instance.term_id,
                                      setting_to_be_modified=form.instance.setting_to_be_modified,
                                      desired_setting=form.instance.desired_setting)
        form.instance.workflow_status = constants.QUEUED
        form.instance.save()

        return response

    def get_success_url(self):
        """
        If the submitted form is valid and was saved, build the url that is used in the redirect to the job listing page
        Check if the resource_link_id is already in the url, otherwise you may get a duplicate resource_link_id,
        depending on the environment you are in
        """
        url = reverse('bulk_course_settings:job_list')
        if 'resource_link_id' not in url:
            url += '?resource_link_id=' + self.request.GET['resource_link_id']
        return url


class BulkSettingsRevertView(LoginRequiredMixin, View):
    """Endpoint used in reverting the given Job for the given school"""

    def get(self, request, school_id, job_id):
        job_has_already_been_reverted = Job.objects.filter(related_job_id=job_id)
        if job_has_already_been_reverted:
            logger.info('Job {} has already been reverted'.format(job_id))
            messages.error(request, 'Job has already been reverted')
        else:
            messages.success(request, 'Reversion job was created successfully')
            related_bulk_job = Job.objects.get(id=job_id)

            new_bulk_job = Job.objects.create(related_job_id=related_bulk_job.id,
                                              school_id=school_id,
                                              term_id=related_bulk_job.term_id,
                                              setting_to_be_modified=related_bulk_job.setting_to_be_modified,
                                              created_by=str(self.request.user))

            utils.queue_bulk_settings_job(bulk_settings_id=new_bulk_job.id, school_id=school_id,
                                          term_id=related_bulk_job.term_id,
                                          setting_to_be_modified=related_bulk_job.setting_to_be_modified,
                                          desired_setting='REVERT')
            new_bulk_job.workflow_status = constants.QUEUED
            new_bulk_job.save()
            logger.info('Queued reversion job {} for related job {}'.format(new_bulk_job.id, related_bulk_job.id))

        url = reverse('bulk_course_settings:job_list')
        if 'resource_link_id' not in url:
            url += '?resource_link_id=' + self.request.GET['resource_link_id']

        return redirect(url)


class BulkSettingsDetailView(LoginRequiredMixin, ListView):
    """Display information regarding the given Job and its Details"""
    model = Job
    template_name = 'bulk_course_settings/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return Job.objects.get(id=self.kwargs['job_id'])

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsDetailView, self).get_context_data(**kwargs)
        original_job_id = self.kwargs['job_id']
        reversion_job = Job.objects.filter(related_job_id=original_job_id).first()
        context['reversion_job'] = reversion_job
        return context
