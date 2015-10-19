from huey.djhuey import crontab, db_periodic_task, db_task
from .models import ISitesExportJob
from datetime import datetime, timedelta
from django.conf import settings
import subprocess
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


@db_task()
def process_job(site_keyword):
    # Pick the first untouched job matching the given keyword, by date
    job = ISitesExportJob.objects.filter(site_keyword=site_keyword,
                                         status=ISitesExportJob.STATUS_NEW).order_by('-created_at')[0]
    # Update job status to In-Progress before proceeding
    job.status = ISitesExportJob.STATUS_IN_PROGRESS
    job.save()
    # Now, make an ssh call to the server hosting the perl script and check output.
    result = ""
    try:
        result = subprocess.check_output(
            ["/usr/bin/ssh",
                '%s@%s' % (settings.EXPORT_TOOL['ssh_user'], settings.EXPORT_TOOL['ssh_hostname']),
                "-i",
                settings.EXPORT_TOOL['ssh_private_key'],
                settings.EXPORT_TOOL['create_site_zip_cmd'],
                "--keyword %s" % site_keyword],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        logger.error("SSH Process Error({0}: {1}".format(cpe.returncode, cpe.output))
        job.status = ISitesExportJob.STATUS_ERROR
        job.output_message = cpe.output[:250]
        job.save()
    else:
        if "Success" in result:
            # Output is in format: Success|filename
            job.status = ISitesExportJob.STATUS_COMPLETE
            job.output_file_name = result.split("|")[1].rstrip('\n\r')
        else:
            # Some kind of error happened, let's log it and store it in the message column
            logger.error("export failed with: %s" % result)
            job.status = ISitesExportJob.STATUS_ERROR
            job.output_message = result[:250]
        # Update job after completion
        job.save()


@db_periodic_task(crontab(**settings.EXPORT_TOOL['archive_task_crontab']))
def archive_jobs():
    # Set up time difference
    days_ago_threshold = datetime.now() - timedelta(hours=settings.EXPORT_TOOL['archive_cutoff_time_in_hours'])
    # Pick jobs that are older than the interval defined in settings and are not already archived
    archivable_jobs = ISitesExportJob.objects.filter(created_at__lt=days_ago_threshold).exclude(status=ISitesExportJob.STATUS_ARCHIVED)
    # Iterate over these jobs and set their status to archived
    for job in archivable_jobs:
        # NOTE: the perl script called during processing stores files in s3 (deleting the local version after
        # upload) so we no longer have to call the remove command
        job.status = ISitesExportJob.STATUS_ARCHIVED
        job.archived_on = datetime.now()
        job.save()
