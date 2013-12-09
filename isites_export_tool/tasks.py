from huey.djhuey import crontab, periodic_task, task
from .models import ISitesExportJob
from datetime import datetime, timedelta
import subprocess, sys, logging

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
        output_file = result.split("|")[1]
        job.status = ISitesExportJob.STATUS_COMPLETE
        job.output_file_name = output_file
    else:
        # Some kind of error happened, let's store it in the message column
        job.status = ISitesExportJob.STATUS_ERROR
        job.output_message = result
        
    # Update job after completion
    job.save()
    

@periodic_task(crontab(day_of_week='1-5', hour='9-17', minute='0'))
def archive_jobs():
    # Set up time difference
    days_ago_threshold = datetime.now() - timedelta(hours=48)
    # Pick jobs that have been completed and are older than the interval defined in settings
    archivable_jobs = ISitesExportJob.objects.filter(status=ISitesExportJob.STATUS_COMPLETE, created_at__lt=days_ago_threshold).order_by('created_at')
    # Iterate over these jobs and set their status to archived
    for job in archivable_jobs:
        job.status = ISitesExportJob.STATUS_ARCHIVED
        job.archived_on = datetime.now()
        job.save()
