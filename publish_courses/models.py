from typing import Dict

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

    school_id = models.CharField(max_length=10)
    term_id = models.CharField(max_length=10, null=True, blank=True)
    workflow_status = models.CharField(max_length=30, choices=WORKFLOW_STATUS, default=constants.NEW)
    created_by_user_id = models.CharField(max_length=15)
    user_full_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bulk_publish_courses_job"

    def __str__(self):
        return f"{{'id': {self.id}, 'school_id': {self.school_id}, 'workflow_status': {self.workflow_status}}}"
    
    def serialize(self) -> Dict:
        """Serialize Job instance for representation as a dictionary."""
        return {
            "id": self.id,
            "school_id": self.school_id,
            "term_id": self.term_id,
            "workflow_status": self.workflow_status,
            "created_by_user_id": self.created_by_user_id,
            "user_full_name": self.user_full_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "job_details_total_count": self.job_details.count(),
            "job_details_success_count": self.job_details.filter(workflow_status=constants.COMPLETED).count(),
            "job_details_failed_count": self.job_details.filter(workflow_status=constants.FAILED).count(),
            "job_details": [detail.serialize() for detail in self.job_details.all()]
        }


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
    post_state = models.CharField(max_length=2000, null=True)
    
    class Meta:
        db_table = "bulk_publish_courses_job_details"

    def __str__(self):
        return f"{{'canvas_course_id': {self.canvas_course_id}, 'workflow_status': {self.workflow_status}, 'post_state': {self.post_state}}}"
    
    def serialize(self) -> Dict:
        """Serialize JobDetails instance for representation as a dictionary."""
        return {
            "parent_job": self.parent_job,
            "canvas_course_id": self.canvas_course_id,
            "workflow_status": self.workflow_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "post_state": self.post_state
        }
