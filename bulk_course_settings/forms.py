import logging

from django import forms

from models import Job

logger = logging.getLogger(__name__)


class CreateBulkSettingsForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['setting_to_be_modified', 'desired_setting', 'school_id', 'term_id']
