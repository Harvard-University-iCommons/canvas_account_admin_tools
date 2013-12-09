from django.conf import settings
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import BaseCreateView
from icommons_common.auth.views import LoginRequiredMixin
from .models import ISitesExportJob, ISitesExportJobForm
from django.core.urlresolvers import reverse_lazy
from .tasks import process_job

# from braces.views import CsrfExemptMixin
# from django.http import HttpResponse
import logging
# import hashlib # Hash encrypt the user's HUID
# import json # Formats form post that user submitted to Piazza
# Get an instance of a logger
logger = logging.getLogger(__name__)

# When setting up a tool in iSites, a POST request is initially made to the tool so we need to mark this entrypoint as exempt from the csrf requirement
class JobListOrCreate(LoginRequiredMixin, TemplateResponseMixin, BaseCreateView):
    template_name = "isites_export_tool/job_list.html"
    form_class = ISitesExportJobForm
    success_url = reverse_lazy('et:job_list')
    archive = False # Whether to display archived jobs or not

    def get_context_data(self, **kwargs):
        context = super(JobListOrCreate, self).get_context_data(**kwargs)

        # Retrieve list of export jobs, archived or no archive, depending on value of instance variable
        if self.archive :
            job_list = ISitesExportJob.objects.filter(status=ISitesExportJob.STATUS_ARCHIVED)
        else :
            job_list = ISitesExportJob.objects.exclude(status=ISitesExportJob.STATUS_ARCHIVED)

        context['jobs'] = job_list
        context['showing_archive'] = self.archive
        return context

    def get_success_url(self):
        logger.info("Inside get_success_url with keyword created of %s" % self.object.site_keyword)
        process_job(self.object.site_keyword) # Kick off queue process
        return super(JobListOrCreate, self).get_success_url()
        
