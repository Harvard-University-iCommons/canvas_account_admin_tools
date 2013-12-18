from huey.djhuey import crontab, periodic_task, task
from .models import ISitesExportJob
from datetime import datetime, timedelta
from django.conf import settings
import subprocess, logging
import os

# Get an instance of a logger
logger = logging.getLogger(__name__)

@task()
def process_job(site_keyword):

    # Pick the first untouched job matching the given keyword, by date
    job = ISitesExportJob.objects.filter(site_keyword=site_keyword, status=ISitesExportJob.STATUS_NEW).order_by('-created_at')[0]
    # Update job status to In-Progress before proceeding
    job.status = ISitesExportJob.STATUS_IN_PROGRESS
    job.save()
    logger.info("before call to subprocess")
    logger.info("environment variables are %s" % os.environ)
    try :
        result = subprocess.check_output(["ssh", settings.EXPORT_TOOL['ssh_hostname'], settings.EXPORT_TOOL['create_site_zip_cmd'], "--keyword %s" % site_keyword],
                                     stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        logger.error("SSH Process Error({0}: {1}".format(cpe.returncode, cpe.output))
        job.status = ISitesExportJob.STATUS_ERROR
        job.output_message = cpe.output    
        job.save()
    else:
        logger.info("after call to subprocess")
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
    days_ago_threshold = datetime.now() - timedelta(hours=settings.EXPORT_TOOL['archive_cutoff_time_in_hours'])
    # Pick jobs that are older than the interval defined in settings
    archivable_jobs = ISitesExportJob.objects.filter(created_at__lt=days_ago_threshold).order_by('created_at')
    # Iterate over these jobs and set their status to archived
    for job in archivable_jobs:
        # For jobs that have been completed and have file output, we will delete the remote file
        if (job.status == ISitesExportJob.STATUS_COMPLETE and job.output_file_name):
            result = subprocess.check_output(["ssh", settings.EXPORT_TOOL['ssh_hostname'], settings.EXPORT_TOOL['remove_site_zip_cmd'], "--filename %s" % job.output_file_name],
                                             stderr=subprocess.STDOUT)

        job.status = ISitesExportJob.STATUS_ARCHIVED
        job.archived_on = datetime.now()
        job.save()
