import logging
from typing import Dict, List

from django.db.models import Count, Q
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

from coursemanager.models import Term, CourseInstance, Course

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
		job_queryset = Job.objects.filter(school_id=school_id)

		# Annotate the Job queryset with counts for each workflow_state
		job_queryset = job_queryset.annotate(
			details_total_count=Count('details'),
			details_success_count=Count('details', filter=Q(details__workflow_status='COMPLETED')),
			details_failed_count=Count('details', filter=Q(details__workflow_status='FAILED')),
			details_skipped_count=Count('details', filter=Q(details__workflow_status='SKIPPED'))
		)

		return job_queryset


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
		"""If the form is valid, create the Job and send it to the queueing lambda"""
		lti_session = getattr(self.request, 'LTI', {})
		audit_user_id = lti_session.get('custom_canvas_user_login_id')
		account_sis_id = lti_session.get('custom_canvas_account_sis_id')
		response = super(BulkSettingsCreateView, self).form_valid(form)
		term = Term.objects.get(term_id=form.instance.term_id)
		meta_term_id = term.meta_term_id()

		form.instance.workflow_status = constants.QUEUED
		form.instance.meta_term_id = meta_term_id
		form.instance.term_name = term.display_name
		form.instance.created_by = audit_user_id

		if not all((audit_user_id, account_sis_id)):
			raise DRFValidationError(
				'Invalid LTI session: custom_canvas_user_login_id and '
				'custom_canvas_account_sis_id required')

		sis_account_id = f'sis_account_id:{account_sis_id}'
		meta_term_id = f'sis_term_id:{meta_term_id}'

		if not all((sis_account_id, meta_term_id)):
			raise DRFValidationError('Both account and term are required')

		job = form.instance
		job.save()

		if job.id is not None:
			job_id = job.id
		else:
			job_id = form.instance.id

		logger.info(f' Creating new Bulk course settings job with ID: {job_id}.')

		# Set other variables to be in the payload
		setting_to_be_modified = job.setting_to_be_modified
		desired_setting = job.desired_setting

		# Get a list of Canvas course ID's for a given term and account
		# Adding support for this tool to work in sub-sub accounts by checking the account_sis_id for dept or coursegroup
		if account_sis_id.startswith('school'):
			canvas_course_id_list_acct_term = (CourseInstance.objects.filter(canvas_course_id__isnull=False,
			                                                                 term=term,
			                                                                 course__school=account_sis_id.removeprefix('school:'))
			                                   .values_list('canvas_course_id', flat=True)).distinct()
		elif account_sis_id.startswith('dept'):
			canvas_course_id_list_acct_term = (CourseInstance.objects.filter(canvas_course_id__isnull=False,
			                                                                 term=term,
			                                                                 course__department=account_sis_id.removeprefix('dept:'))
			                                   .values_list('canvas_course_id', flat=True)).distinct()
		else:
			canvas_course_id_list_acct_term = (CourseInstance.objects.filter(canvas_course_id__isnull=False,
			                                                                 term=term,
			                                                                 course__course_group=account_sis_id.removeprefix('coursegroup:'))
			                                   .values_list('canvas_course_id', flat=True)).distinct()

		# Create job details from unpublished courses list
		job_details_list = _create_job_details(job=job, course_id_list=canvas_course_id_list_acct_term)

		# Send job to queueing lambda
		utils.send_job_to_queueing_lambda(job_id, job_details_list, setting_to_be_modified, desired_setting)

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


class BulkSettingsRevertView(LTIPermissionRequiredMixin, LoginRequiredMixin, View):
	"""Endpoint used in reverting the given Job for the given school"""
	permission = 'bulk_course_settings'

	def get(self, request, school_id, job_id):
		job_has_already_been_reverted = Job.objects.filter(related_job_id=job_id)
		if job_has_already_been_reverted:
			logger.info('Job {} has already been reverted'.format(job_id))
			messages.error(request, 'Job has already been reverted')
		else:
			related_bulk_job = Job.objects.get(id=job_id)
			setting_to_be_modified = related_bulk_job.setting_to_be_modified

			reverse_desired_setting_mapping = {
				'False': 'True',
				'True': 'False'
			}

			desired_setting = reverse_desired_setting_mapping[related_bulk_job.desired_setting]

			new_bulk_job = Job.objects.create(related_job_id=related_bulk_job.id,
			                                  school_id=school_id,
			                                  term_id=related_bulk_job.term_id,
			                                  meta_term_id=related_bulk_job.meta_term_id,
			                                  setting_to_be_modified=setting_to_be_modified,
			                                  desired_setting=desired_setting,
			                                  created_by=str(self.request.user))

			new_bulk_job.workflow_status = constants.QUEUED
			new_bulk_job.save()

			related_job_details_course_id_list = (Details.objects.filter(parent_job=related_bulk_job.id).
			                                      exclude(workflow_status=constants.SKIPPED).
			                                      values_list('canvas_course_id', flat=True))

			job_details_list = _create_job_details(job=new_bulk_job, course_id_list=related_job_details_course_id_list)

			utils.send_job_to_queueing_lambda(related_bulk_job.id, job_details_list, setting_to_be_modified, desired_setting)

			# logger.info('Queued reversion job {} for related job {}'.format(new_bulk_job.id, related_bulk_job.id))
			messages.success(request, 'Reversion job was created successfully')

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
		job_queryset = Job.objects.filter(id=self.kwargs['job_id'])

		# Annotate the Job queryset with counts for each workflow_state
		job_queryset = job_queryset.annotate(
			details_total_count=Count('details'),
			details_success_count=Count('details', filter=Q(details__workflow_status='COMPLETED')),
			details_failed_count=Count('details', filter=Q(details__workflow_status='FAILED')),
			details_skipped_count=Count('details', filter=Q(details__workflow_status='SKIPPED'))
		)

		return job_queryset[0]

	def get_context_data(self, **kwargs):
		context = super(BulkSettingsDetailView, self).get_context_data(**kwargs)
		original_job_id = self.kwargs['job_id']
		reversion_job = Job.objects.filter(related_job_id=original_job_id).first()
		context['reversion_job'] = reversion_job

		return context


def _create_job_details(job: Job, course_id_list: List[int]) -> List[Dict]:
	job_details_list = []

	# Create Details objects to efficiently insert all objects into the database in a single query.
	job_details_objects = [Details(parent_job_id=job.id, canvas_course_id=course_id) for course_id in course_id_list]
	just_created_job_objects = Details.objects.bulk_create(job_details_objects)  # Bulk create Details objects (save to database).
	logger.info(f'Creating job info for job ID {job.id} to database.')

	# Create object that will be sent to queueing lambda
	for job_detail in just_created_job_objects:
		job_details_list.append(
			{
				"job_detail_id": job_detail.id,
				"course_id": job_detail.canvas_course_id
			}
		)

	return job_details_list
