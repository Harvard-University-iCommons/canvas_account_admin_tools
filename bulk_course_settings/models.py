import logging
from django.db import models
from django.urls import reverse

from coursemanager.models import Term

from bulk_course_settings import constants


logger = logging.getLogger(__name__)


class Job(models.Model):
    """
    Master table to manage bulk changes to course settings
    """

    DESIRED_SETTING_CHOICES = (
        ('True', 'True'),
        ('False', 'False')
    )

    SETTINGS_TO_MODIFY_CHOICES = (
        ('is_public', 'Course is open to the public'),
        ('is_public_to_auth_users', 'Course is open to all authenticated users'),
        ('public_syllabus', 'Syllabus is open to the public'),
        ('public_syllabus_to_auth', 'Syllabus is open to all authenticated users')
    )

    WORKFLOW_STATUS = (
        (constants.NEW, 'New'),
        (constants.QUEUED, 'Queued'),
        (constants.IN_PROGRESS, 'In progress'),
        (constants.COMPLETED_SUCCESS, 'Completed successfully'),
        (constants.COMPLETED_ERRORS, 'Completed with errors'),
        (constants.FAILED, 'Failed')
    )

    school_id = models.CharField(max_length=10)
    term_id = models.IntegerField(null=True, blank=True)
    setting_to_be_modified = models.CharField(max_length=50, choices=SETTINGS_TO_MODIFY_CHOICES, default='is_public')
    desired_setting = models.CharField(max_length=50, choices=DESIRED_SETTING_CHOICES, default='True')
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default=constants.NEW)
    related_job_id = models.IntegerField(null=True)
    created_by = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    details_total_count = models.IntegerField(default=0)
    details_success_count = models.IntegerField(default=0)
    details_failed_count = models.IntegerField(default=0)
    details_skipped_count = models.IntegerField(default=0)

    def get_term_name(self):
        term = Term.objects.get(term_id=int(self.term_id))
        return term.display_name


class Details(models.Model):
    """
    Details for each bulk course settings job run
    """

    WORKFLOW_STATUS = (
        (constants.NEW, 'New'),
        (constants.SKIPPED, 'Skipped'),
        (constants.COMPLETED, 'Completed'),
        (constants.FAILED, 'Failed')
    )

    parent_job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='details')
    canvas_course_id = models.IntegerField(null=True, blank=True)
    current_setting_value = models.CharField(max_length=20, null=True, blank=True)
    prior_state = models.CharField(max_length=2000, null=True)
    post_state = models.CharField(max_length=2000, null=True)
    workflow_status = models.CharField(max_length=20, choices=WORKFLOW_STATUS, default=constants.NEW)
    is_modified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
