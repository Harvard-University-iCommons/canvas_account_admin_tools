from django.conf import settings
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import BaseCreateView
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect

from icommons_common.auth.decorators import group_membership_restriction
from icommons_common.auth.views import GroupMembershipRequiredMixin
from icommons_common.monitor.views import BaseMonitorResponseView

from .models import ISitesExportJob, ISitesExportJobForm
from .tasks import process_job

import boto

# from braces.views import CsrfExemptMixin
# from django.http import HttpResponse
import logging
# import hashlib # Hash encrypt the user's HUID
# import json # Formats form post that user submitted to Piazza
# Get an instance of a logger
logger = logging.getLogger(__name__)

# When setting up a tool in iSites, a POST request is initially made to the
# tool so we need to mark this entrypoint as exempt from the csrf requirement


class JobListView(GroupMembershipRequiredMixin, TemplateResponseMixin, BaseCreateView):
    allowed_groups = settings.EXPORT_TOOL['allowed_groups']
    template_name = "isites_export_tool/job_list.html"
    form_class = ISitesExportJobForm
    success_url = reverse_lazy('et:job_list')
    archive = False  # Whether to display archived jobs or not

    def get_form_kwargs(self):
        # Ensure the current `request` is provided to ISitesExportJobForm.
        kwargs = super(JobListView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(JobListView, self).get_context_data(**kwargs)

        # Retrieve list of export jobs, archived or no archive, depending on value of instance variable
        if self.archive:
            job_list = ISitesExportJob.objects.filter(status=ISitesExportJob.STATUS_ARCHIVED)
        else:
            job_list = ISitesExportJob.objects.exclude(status=ISitesExportJob.STATUS_ARCHIVED)

        context['jobs'] = job_list
        context['showing_archive'] = self.archive
        return context

    def get_success_url(self):
        logger.info("Inside get_success_url with keyword created of %s" % self.object.site_keyword)
        process_job(self.object.site_keyword)  # Kick off queue process
        return super(JobListView, self).get_success_url()


class MonitorResponseView(BaseMonitorResponseView):
    def healthy(self):
        return True


@login_required
@group_membership_restriction(allowed_groups=settings.EXPORT_TOOL.get('allowed_groups', ''))
def download_export_file(request, export_filename):
    # Per http://boto.readthedocs.org/en/latest/boto_config_tut.html there are number of ways to
    # for boto to retrieve credentials (AWS access key and seceret).  For our AWS servers with IAM
    # roles that grant access to s3 buckets, we use the metadata service.  For local environments,
    # you can create a .boto file with credentials or set environment variables.
    try:
        s3 = boto.connect_s3()
    except boto.exception.NoAuthHandlerFound:
        logger.exception('Error while trying to connect to s3 service')

    # From http://boto.readthedocs.org/en/latest/ref/s3.html#boto.s3.connection.S3Connection.generate_url
    # Once the connection is established above, this method will happily create a link using whatever
    # options given.  If the link is bad (e.g. credentials are bad, bucket doesn't exist, etc.) the end
    # user will see a corresponding error page from AWS.
    file_download_url = s3.generate_url(
        settings.EXPORT_TOOL['s3_download_url_expiration_in_secs'],  # How long url is good for
        'GET',
        settings.EXPORT_TOOL['s3_bucket'],
        export_filename
    )

    return redirect(file_download_url)
