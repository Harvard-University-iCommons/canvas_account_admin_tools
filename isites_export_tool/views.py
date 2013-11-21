from django.conf import settings
from django.views.generic.list import ListView
from .models import ISitesExportJob

# from braces.views import CsrfExemptMixin
# from django.http import HttpResponse
import logging
# import hashlib # Hash encrypt the user's HUID
# import json # Formats form post that user submitted to Piazza
# Get an instance of a logger
logger = logging.getLogger(__name__)

# When setting up a tool in iSites, a POST request is initially made to the tool so we need to mark this entrypoint as exempt from the csrf requirement
class JobsIndexView(ListView):
    template_name = "job_index.html"
    context_object_name = 'jobs'
    queryset = ISitesExportJob.objects.all()
