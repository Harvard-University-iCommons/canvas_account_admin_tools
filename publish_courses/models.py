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
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default=constants.NEW)
    created_by_user_id = models.CharField(max_length=15)
    user_full_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bulk_publish_courses_job"

    def __str__(self):
        return f"{{'id': {self.id}, 'school_id': {self.school_id}, 'workflow_status': {self.workflow_status}}}"


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
