import logging

from django import forms

from .models import Job

logger = logging.getLogger(__name__)


class CreateBulkSettingsForm(forms.ModelForm):
	class Meta:
		model = Job
		fields = ['setting_to_be_modified', 'desired_setting', 'term_id']

	def __init__(self, *args, **kwargs):
		super(CreateBulkSettingsForm, self).__init__(*args, **kwargs)
		for field in self.fields.values():
			field.widget.attrs['class'] = 'form-control'
