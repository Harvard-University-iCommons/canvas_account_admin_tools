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
import utils

logger = logging.getLogger(__name__)

# TODO pull this out into utils
JOB_QUEUE_NAME = settings.BULK_COURSE_SETTINGS['job_queue_name']


def lti_auth_error(request):
    raise PermissionDenied


class BulkSettingsListView(generic.ListView):
    model = BulkCourseSettingsJob
    template_name = 'bulk_course_settings/bulk_settings_list.html'
    context_object_name = 'bulk_settings_list'
    queryset = BulkCourseSettingsJob.objects.all()

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsListView, self).get_context_data(**kwargs)
        return context


class BulkSettingsCreateView(CreateView, FormView):

    form_class = CreateBulkSettingsForm
    template_name = 'bulk_course_settings/create_new_setting.html'
    context_object_name = 'create_new_setting'
    model = BulkCourseSettingsJob

    def get_context_data(self, **kwargs):
        context = super(BulkSettingsCreateView, self).get_context_data(**kwargs)
        # account_sis_id = self.request.LTI['custom_canvas_account_sis_id']
        account_sis_id = 'school:hks'
        context['account_sis_id'] = account_sis_id
        context['school_id'] = account_sis_id.split(':')[1]
        context['terms'] = utils.get_term_data_for_school(account_sis_id)
        return context

    def form_valid(self, form):
        # If the form is valid, create the BulkCourseSettingsJob and add it to the SQS queue
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        response = super(BulkSettingsCreateView, self).form_valid(form)

        utils.queue_bulk_settings_job(bulk_settings_id=form.instance.id, school_id=form.instance.school_id,
                                      term_id=form.instance.term_id,
                                      setting_to_be_modified=form.instance.setting_to_be_modified,
                                      desired_setting=form.instance.desired_setting)

        return response


class BulkSettingsRevertView(generic.edit.CreateView):
    form_class = ""
