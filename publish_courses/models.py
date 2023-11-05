from django.db import models

from publish_courses import constants


class Job(models.Model):
    """
    Main table to manage bulk publish courses jobs.
    """

    WORKFLOW_STATUS = (
        (constants.NEW, 'New'),
        (constants.QUEUED, 'Queued'),
        (constants.IN_PROGRESS, 'In progress'),
        (constants.COMPLETED_SUCCESS, 'Completed successfully'),
        (constants.COMPLETED_ERRORS, 'Completed with errors'),
        (constants.FAILED, 'Failed')
    )

    job = models.CharField(max_length=80, unique=True)
    school_id = models.CharField(max_length=10)
    term_id = models.CharField(max_length=10, null=True, blank=True)
    workflow_state = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default=constants.NEW)
    created_by_user_id = models.CharField(max_length=15)
    user_full_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    job_details_total_count = models.PositiveIntegerField(default=0)
    job_details_failed_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "bulk_publish_courses_job"

    def serialize(self):
        return {
            "job": self.job,
            "school_id": self.school_id,
            "term_id": self.term_id,
            "workflow_state": self.workflow_state,
            "created_by_user_id": self.created_by_user_id,
            "user_full_name": self.user_full_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "job_details_total_count": self.job_details_total_count,
            "job_details_failed_count": self.job_details_failed_count,
            "job_details": [detail.serialize() for detail in self.job_details.all()]
        }

    def __str__(self):
        return f"Job {self.job}"


class JobDetails(models.Model):
    """
    Details for each bulk publish courses job run.
    """

    WORKFLOW_STATUS = (
        (constants.NEW, 'New'),
        (constants.SKIPPED, 'Skipped'),
        (constants.COMPLETED, 'Completed'),
        (constants.FAILED, 'Failed')
    )

    parent_job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_details')
    canvas_course_id = models.PositiveIntegerField()
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default=constants.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    prior_state = models.CharField(max_length=2000, null=True)
    post_state = models.CharField(max_length=2000, null=True)
    

    class Meta:
        db_table = "bulk_publish_courses_job_details"

    def serialize(self):
        return {
            "parent_job": self.parent_job,
            "canvas_course_id": self.canvas_course_id,
            "workflow_status": self.workflow_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "prior_state": self.prior_state,
            "post_state": self.post_state
        }

    def __str__(self):
        return f"Job Details for Job {self.job_record.job}"
