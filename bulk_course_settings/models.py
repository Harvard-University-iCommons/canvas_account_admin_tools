import logging
from django.db import models
from django.urls import reverse

# from bulk_course_settings.utils import get_term_data
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
        ('is_public', 'is_public'),
        ('is_public_to_auth_users', 'is_public_to_auth_users'),
        ('public_syllabus', 'public_syllabus'),
        ('public_syllabus_to_auth', 'public_syllabus_to_auth')
    )

    WORKFLOW_STATUS = (
        ('IN_PROGRESS', 'In progress'),
        ('QUEUED', 'Queued'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    )

    school_id = models.CharField(max_length=10)
    term_id = models.IntegerField(null=True, blank=True)
    setting_to_be_modified = models.CharField(max_length=20, choices=SETTINGS_TO_MODIFY_CHOICES, default='is_public')
    #current_setting_state = models.CharField(max_length=11, null=True, blank=True)
    desired_setting = models.BooleanField(choices=DESIRED_SETTING_CHOICES, default=True)
    workflow_status= models.CharField(max_length=20, choices=WORKFLOW_STATUS, default='IN_PROGRESS')
    related_job_id = models.IntegerField(null=True)
    created_by = models.CharField(max_length=15)
    updated_by = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_absolute_url():
        return reverse('bulk_course_settings:bulk_settings_list')

    def get_term_name(self):
        return get_term_data(self.term_id)['name']


class BulkCourseSettingsJobDetails(models.Model):
    """
    Details for each bulk course settings job run
    """
    parent_job_process_id = models.ForeignKey(BulkCourseSettingsJob, on_delete=models.CASCADE)
    canvas_course_id = models.IntegerField(null=True, blank=True)
    current_setting_value = models.CharField(max_length=20, null=True, blank=True)
    # new_setting_value = models.CharField(max_length=20, null=True, blank=True)
    current_course_attributes = models.CharField(max_length=200)
    new_course_attributes = models.CharField(max_length=200)
    workflow_status = models.CharField(max_length=200)
    is_modified = models.BooleanField(default=False)
    created_by = models.CharField(max_length=15)
    updated_by = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


def get_term_data(term_id):
    term = Term.objects.get(term_id=int(term_id))
    return {
        'id': str(term.term_id),
        'name': term.display_name,
    }
