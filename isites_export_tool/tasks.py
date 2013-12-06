from huey.djhuey import crontab, periodic_task, task
from .models import ISitesExportJob
import subprocess
import sys
import logging
# import hashlib # Hash encrypt the user's HUID
# import json # Formats form post that user submitted to Piazza
# Get an instance of a logger
logger = logging.getLogger(__name__)


HOST = "isites-qa"
COMMAND = "/u02/icommons/perlapps/iSitesAPI/scripts/export_site_files_zip.pl"

@task()
def process_job(site_keyword):

    # Pick the first untouched job matching the given keyword, by date
    job = ISitesExportJob.objects.filter(site_keyword=site_keyword, status=ISitesExportJob.STATUS_NEW).order_by('-created_at')[0]
    # Update job status to In-Progress before proceeding
    job.status = ISitesExportJob.STATUS_IN_PROGRESS
    job.save()
    result = subprocess.check_output(["ssh", HOST, COMMAND, "--keyword %s" % site_keyword],
                                     stderr=subprocess.STDOUT)
    
    if (result.startswith("Success")):
        # Output is in format: Success|filename
        logger.info("before call to subprocess")

        output_file = result.split("|")[1]
        job.status = ISitesExportJob.STATUS_COMPLETE
        job.output_file_name = output_file
        job.save()
    else:
        # Some kind of error happened, let's store it in the message column
        job.status = ISitesExportJob.STATUS_ERROR
        job.output_message = result
        job.save()
    
