import logging

from django.db import models

logger = logging.getLogger(__name__)

class BulkCourseSettingsJob(models.Model):
    """
    master table to manage bulk changes to course settings
    """

    DESIRED_VISIBILITY_CHOICES = (
        ('COURSE', 'course'),
        ('INSTITUTION', 'Harvard'),
        ('PUBLIC', 'public'),
    )

    SETTINGS_TO_MODIFY_CHOICES = (
        ('COURSE_VISIBILITY', 'Course Visibility'),
        ('SYLLABUS_VISIBILITY', 'Syllabus Visibility'),
        ('QUOTA', 'Course Quota'),
    )

    school_id = models.CharField(max_length=10)
    term_id = models.IntegerField(null=True, blank=True)
    setting_to_be_modified = models.CharField(max_length=20, choices=SETTINGS_TO_MODIFY_CHOICES, default='Course Visibility')
    #current_setting_state = models.CharField(max_length=11, null=True, blank=True)
    desired_setting = models.CharField(max_length=11, choices=DESIRED_VISIBILITY_CHOICES, default='course')
    workflow_status= models.CharField(max_length=20)
    parent_process_id = models.IntegerField(null=True)
    created_by = models.CharField(max_length=15)
    updated_by = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

class BulkCourseSettingsJobDetails(models.Model):
    """
    details for each bulk course settings job run
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
