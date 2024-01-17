import logging
from typing import Dict, List

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from harvardkey_cas.mixins import LoginRequiredMixin
from lti_school_permissions.mixins import LTIPermissionRequiredMixin
from rest_framework.exceptions import ValidationError as DRFValidationError

from bulk_course_settings import constants, utils
from bulk_course_settings.forms import CreateBulkSettingsForm
from bulk_course_settings.models import Job, Details

from coursemanager.models import Term

logger = logging.getLogger(__name__)


def lti_auth_error(request):
    raise PermissionDenied


class BulkSettingsListView(LTIPermissionRequiredMixin, LoginRequiredMixin, ListView):
    """Display a table with all Jobs created from this account."""
    model = Job
    template_name = 'bulk_course_settings/job_list.html'
    context_object_name = 'jobs'
    permission = 'bulk_course_settings'

    def get_queryset(self):
        account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        school_id = account_sis_id.split(':')[1]
        return Job.objects.filter(school_id=school_id)


class BulkSettingsCreateView(LTIPermissionRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):

    """Displays the form used to create a Job with the desired setting and value"""
    form_class = CreateBulkSettingsForm
    template_name = 'bulk_course_settings/create_new_job.html'
    model = Job
    success_message = 'Job was created successfully'
    permission = 'bulk_course_settings'

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
        term = Term.objects.get(term_id=form.instance.term_id)
        meta_term_id = term.meta_term_id()

        utils.queue_bulk_settings_job(bulk_settings_id=form.instance.id, school_id=form.instance.school_id,
                                      meta_term_id=meta_term_id,
                                      setting_to_be_modified=form.instance.setting_to_be_modified,
                                      desired_setting=form.instance.desired_setting)
        form.instance.workflow_status = constants.QUEUED
        form.instance.meta_term_id = meta_term_id
        form.instance.save()

        return response
    
    def create_job_details(self, job: Job, unpublished_courses: List[int]) -> Dict:
        job_details_list = []

        # Create Details objects to efficiently insert all objects into the database in a single query.
        job_details_objects = [Details(parent_job_id=job.id, canvas_course_id=course_id) for course_id in unpublished_courses]
        just_created_job_objects = Details.objects.bulk_create(job_details_objects)  # Bulk create Details objects (save to database).
        logger.info(f'Creating job info for job ID {job.id} to database.')

        # Create object that will be sent to queueing lambda
        for job_detail in just_created_job_objects:
            job_details_list.append(
                {
                    "job_detail_id": job_detail.id,
                    "canvas_course_id": job_detail.canvas_course_id
                }
            )

        return job_details_list
        
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


class BulkSettingsRevertView(LTIPermissionRequiredMixin, LoginRequiredMixin, View):
    """Endpoint used in reverting the given Job for the given school"""
    permission = 'bulk_course_settings'

    def get(self, request, school_id, job_id):
        job_has_already_been_reverted = Job.objects.filter(related_job_id=job_id)
        if job_has_already_been_reverted:
            logger.info('Job {} has already been reverted'.format(job_id))
            messages.error(request, 'Job has already been reverted')
        else:
            messages.success(request, 'Reversion job was created successfully')
            related_bulk_job = Job.objects.get(id=job_id)

            reverse_desired_setting_mapping = {
                'False': 'True',
                'True': 'False'
            }

            new_bulk_job = Job.objects.create(related_job_id=related_bulk_job.id,
                                              school_id=school_id,
                                              term_id=related_bulk_job.term_id,
                                              meta_term_id=related_bulk_job.meta_term_id,
                                              setting_to_be_modified=related_bulk_job.setting_to_be_modified,
                                              desired_setting=reverse_desired_setting_mapping[related_bulk_job.desired_setting],
                                              created_by=str(self.request.user))

            utils.queue_bulk_settings_job(bulk_settings_id=new_bulk_job.id, school_id=school_id,
                                          meta_term_id=related_bulk_job.meta_term_id,
                                          setting_to_be_modified=related_bulk_job.setting_to_be_modified,
                                          desired_setting='REVERT')
            new_bulk_job.workflow_status = constants.QUEUED
            new_bulk_job.save()
            logger.info('Queued reversion job {} for related job {}'.format(new_bulk_job.id, related_bulk_job.id))

        url = reverse('bulk_course_settings:job_list')
        if 'resource_link_id' not in url:
            url += '?resource_link_id=' + self.request.GET['resource_link_id']

        return redirect(url)


class BulkSettingsDetailView(LTIPermissionRequiredMixin, LoginRequiredMixin, ListView):
    """Display information regarding the given Job and its Details"""
    model = Job
    template_name = 'bulk_course_settings/job_detail.html'
    context_object_name = 'job'
    permission = 'bulk_course_settings'

    def get_queryset(self):
        return Job.objects.get(id=self.kwargs['job_id'])

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsDetailView, self).get_context_data(**kwargs)
        original_job_id = self.kwargs['job_id']
        reversion_job = Job.objects.filter(related_job_id=original_job_id).first()
        context['reversion_job'] = reversion_job
        return context
