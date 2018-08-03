import logging
from django.db import models
from django.urls import reverse

from icommons_common.models import Term


logger = logging.getLogger(__name__)


class BulkCourseSettingsJob(models.Model):
    """
    Master table to manage bulk changes to course settings
    """

    DESIRED_SETTING_CHOICES = (
        (True, 'True'),
        (False, 'False')
    )

    SETTINGS_TO_MODIFY_CHOICES = (
        ('is_public', 'Course is public'),
        ('is_public_to_auth_users', 'Course is public to auth users'),
        ('public_syllabus', 'Public syllabus'),
        ('public_syllabus_to_auth', 'Syllabus is public to auth users')
    )

    WORKFLOW_STATUS = (
        ('NEW', 'New'),
        ('QUEUED', 'Queued'),
        ('IN_PROGRESS', 'In progress'),
        ('COMPLETED_SUCCESS', 'Completed Success'),
        ('COMPLETED_ERRORS', 'Completed Errors'),
        ('FAILED', 'Failed')
    )

    school_id = models.CharField(max_length=10)
    term_id = models.IntegerField(null=True, blank=True)
    setting_to_be_modified = models.CharField(max_length=20, choices=SETTINGS_TO_MODIFY_CHOICES, default='is_public')
    desired_setting = models.BooleanField(choices=DESIRED_SETTING_CHOICES, default=True)
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default='NEW')
    related_job_id = models.IntegerField(null=True)
    created_by = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bulk_course_settings_job'

    @staticmethod
    def get_absolute_url():
        return reverse('bulk_course_settings:bulk_settings_list')

    def get_term_name(self):
        term = Term.objects.get(term_id=int(self.term_id))
        return term.display_name


class BulkCourseSettingsJobDetails(models.Model):
    """
    Details for each bulk course settings job run
    """

    # TODO make this the choices for workflow
    WORKFLOW_STATUS = (
        ('NEW', 'New'),
        ('SKIPPED', 'Skipped'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    )

    parent_job_process_id = models.ForeignKey(BulkCourseSettingsJob, on_delete=models.CASCADE)
    canvas_course_id = models.IntegerField(null=True, blank=True)
    current_setting_value = models.CharField(max_length=20, null=True, blank=True)
    prior_state = models.CharField(max_length=2000, null=True)
    post_state = models.CharField(max_length=2000, null=True)
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default='NEW')
    is_modified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bulk_course_settings_job_details'
