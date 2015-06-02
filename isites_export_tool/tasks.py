from huey.djhuey import crontab, periodic_task, task
from .models import ISitesExportJob
from datetime import datetime, timedelta
from django.conf import settings
import subprocess
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


@task()
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
        job.output_message = cpe.output
        job.save()
    else:
        if (result.startswith("Success")):
            # Output is in format: Success|filename
            job.status = ISitesExportJob.STATUS_COMPLETE
            job.output_file_name = result.split("|")[1]
        else:
            # Some kind of error happened, let's store it in the message column
            job.status = ISitesExportJob.STATUS_ERROR
            job.output_message = result
        # Update job after completion
        job.save()


@periodic_task(crontab(hour=settings.EXPORT_TOOL['archive_task_crontab_hours']))
def archive_jobs():
    # Set up time difference
    days_ago_threshold = datetime.now() - timedelta(hours=settings.EXPORT_TOOL['archive_cutoff_time_in_hours'])
    # Pick jobs that are older than the interval defined in settings and are not already archived
    archivable_jobs = ISitesExportJob.objects.filter(created_at__lt=days_ago_threshold).exclude(status=ISitesExportJob.STATUS_ARCHIVED)
    # Iterate over these jobs and set their status to archived
    for job in archivable_jobs:
        # For jobs that have been completed and have file output, we will delete the remote file
        if (job.status == ISitesExportJob.STATUS_COMPLETE and job.output_file_name):
            try:
                subprocess.check_output(
                    ["/usr/bin/ssh",
                        '%s@%s' % (settings.EXPORT_TOOL['ssh_user'], settings.EXPORT_TOOL['ssh_hostname']),
                        "-i", settings.EXPORT_TOOL['ssh_private_key'],
                        settings.EXPORT_TOOL['remove_site_zip_cmd'],
                        "--filename %s" % job.output_file_name],
                    stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as cpe:
                logger.error("SSH Process Error({0}: {1}".format(cpe.returncode, cpe.output))
                raise

        job.status = ISitesExportJob.STATUS_ARCHIVED
        job.archived_on = datetime.now()
        job.save()
