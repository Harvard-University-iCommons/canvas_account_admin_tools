# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.utils import timezone
from rq import get_current_job

from async.models import Process
from bulk_utilities.bulk_course_settings import BulkCourseSettingsOperation


logger = logging.getLogger(__name__)


def bulk_publish_canvas_sites(process_id, account=None, course_list=None,
                              term=None, published=True, dry_run=False):
    logger.info("Starting bulk_publish_canvas_sites job {}".format(process_id))

    job = None

    try:
        job = get_current_job()
        job.meta['process_id'] = process_id
        job.save()
        logger.debug("RQ job details: {}".format(job.to_dict()))
    except Exception as e:
        logger.exception(
            "Failed to get current job information from RQ for process_id: {}. "
            "(Possibly running bulk_publish_canvas_sites() outside of an RQ "
            "worker?)".format(process_id))

    try:
        process = Process.objects.get(id=process_id)
    except Process.DoesNotExist:
        logger.exception(
            "Failed to find Process with id {}".format(process_id))
        raise

    op_config = {
        'published': 'true' if published else None,
        'account': account,
        'courses': course_list,
        'term': term,
        'dry_run': dry_run
    }
    process.state = Process.ACTIVE
    process.details['rq_job_id'] = getattr(job, 'id', 'None')
    process.details['op_config'] = op_config
    process.date_active = timezone.now()
    process.save(update_fields=['state', 'details', 'date_active'])

    op = BulkCourseSettingsOperation(op_config)
    try:
        op.execute()
    except Exception as e:
        logger.exception("bulk_publish_canvas_sites job {} "
                         "failed".format(process_id))
        process.status = 'failed'
        process.details['error'] = str(e)

    process.details['stats'] = op.get_stats_dict()
    process.state = Process.COMPLETE
    process.date_complete = timezone.now()
    process.save(update_fields=['state', 'status', 'details', 'date_complete'])

    logger.info("Finished bulk_publish_canvas_sites job {}".format(process_id))
    return process
