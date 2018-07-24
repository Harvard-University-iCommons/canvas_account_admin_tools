from datetime import datetime, time, date
import logging

#from crispy_forms.bootstrap import FormActions
#from crispy_forms.helper import FormHelper
#from crispy_forms.layout import HTML, Field, Fieldset, Layout, Submit
from django import forms
from django.core.urlresolvers import reverse
from bulk_course_settings.models import BulkCourseSettingsJob, BulkCourseSettingsJobDetails
from icommons_common.models import Term, TermCode, School

logger = logging.getLogger(__name__)

class CreateBulkSettingsForm(forms.ModelForm):
    class Meta:
        model = BulkCourseSettingsJob
        fields = ['setting_to_be_modified', 'desired_setting', 'school_id']
        widgets = {
            'school_id': forms.HiddenInput,
        }


