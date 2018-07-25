import logging
from django import forms
from bulk_course_settings.models import BulkCourseSettingsJob

logger = logging.getLogger(__name__)


class CreateBulkSettingsForm(forms.ModelForm):
    class Meta:
        model = BulkCourseSettingsJob
        fields = ['setting_to_be_modified', 'desired_setting', 'school_id']
