from django import forms
#import floppyforms as forms
from icommons_common_data.models import Term,TermCode,School


class EditTermForm(forms.ModelForm):

	# this is a model form that's mostly automatically generated; here we specify that it should be based on the Term model:
	class Meta:
		model = Term

	# make the school, term_code and academic_year fields hidden; they should not be changed once the term is created
	school = forms.ModelChoiceField(queryset=School.objects.all(), widget=forms.widgets.HiddenInput())
	term_code = forms.ModelChoiceField(queryset=TermCode.objects.all(), widget=forms.widgets.HiddenInput())
	academic_year = forms.IntegerField(widget=forms.widgets.HiddenInput())

	# make some additional fields required; they're not strictly required in the database, but we want them to be required here
	start_date = forms.DateField(required=True)
	end_date = forms.DateField(required=True)
	xreg_start_date = forms.DateField(required=True)
	xreg_end_date = forms.DateField(required=True)

	"""
	override the clean method so that we can perform custom validation; this is done at the form level because some validation 
	rules depend on the values of multiple fields. 
	"""
	def clean(self):
		cleaned_data = super(EditTermForm, self).clean()
		school_id = cleaned_data.get('school')
		term_code = cleaned_data.get('term_code')
		academic_year = cleaned_data.get('academic_year')
		calendar_year = cleaned_data.get('calendar_year')
		start_date = cleaned_data.get('start_date')
		end_date = cleaned_data.get('end_date')
		xreg_start_date = cleaned_data.get('start_date')
		xreg_end_date = cleaned_data.get('end_date')
		display_name = cleaned_data.get('display_name')

		# default the display_name if it's not set
		if display_name == None or display_name == '':
			cleaned_data['display_name'] = '{0} {1}'.format(term_code.term_name, academic_year)

		# make sure that the start date is before the end date
		if xreg_start_date and xreg_end_date and start_date > end_date:
			raise forms.ValidationError("The start date must be before the end date.")

		# make sure that the xreg start date is before the xreg end date
		if xreg_start_date and xreg_end_date and xreg_start_date > xreg_end_date:
			raise forms.ValidationError("The xreg start date must be before the xreg end date.")


		# check to make sure that the calendar_year matches the start_date
		if calendar_year and start_date and calendar_year != start_date.year:
			msg = u"The calendar year must match the year in the start date."
			self._errors['calendar_year'] = self.error_class([msg])	
			del cleaned_data['calendar_year']

		return cleaned_data

	
class CreateTermForm(forms.ModelForm):

	# this is a model form that's mostly automatically generated; here we specify that it should be based on the Term model:
	class Meta:
		model = Term

	# make the school field hidden; it's set based on the school ID that appears in the URL and shoudn't be changed by the user
	school = forms.ModelChoiceField(queryset=School.objects.all(), widget=forms.widgets.HiddenInput())

	# make some additional fields required; they're not strictly required in the database, but we want them to be required here
	start_date = forms.DateField(required=True)
	end_date = forms.DateField(required=True)
	xreg_start_date = forms.DateField(required=True)
	xreg_end_date = forms.DateField(required=True)

	"""
	override the clean method so that we can perform custom validation; this is done at the form level because some validation 
	rules depend on the values of multiple fields. 
	"""
	def clean(self):
		cleaned_data = super(CreateTermForm, self).clean()
		school_id = cleaned_data.get('school')
		term_code = cleaned_data.get('term_code')
		academic_year = cleaned_data.get('academic_year')
		calendar_year = cleaned_data.get('calendar_year')
		start_date = cleaned_data.get('start_date')
		end_date = cleaned_data.get('end_date')
		xreg_start_date = cleaned_data.get('start_date')
		xreg_end_date = cleaned_data.get('end_date')
		display_name = cleaned_data.get('display_name')


		# check to see if this term already exists.
		if Term.objects.filter(school_id=school_id.school_id, term_code=term_code.term_code, academic_year=academic_year): 
			raise forms.ValidationError("A term record already exists for this school/year/term_code")

		# default the display_name if it's not set
		if display_name == None or display_name == '':
			cleaned_data['display_name'] = '{0} {1}'.format(term_code.term_name, academic_year)

		# make sure that the start date is before the end date
		if start_date and end_date and start_date > end_date:
			raise forms.ValidationError("The start date must be before the end date.")

		# make sure that the xreg start date is before the xreg end date
		if xreg_start_date and xreg_end_date and xreg_start_date > xreg_end_date:
			raise forms.ValidationError("The xreg start date must be before the xreg end date.")


		# check to make sure that the calendar_year matches the start_date
		if calendar_year and start_date and calendar_year != start_date.year:
			#raise forms.ValidationError("The calendar year must match the year from the start date.")
			msg = u"The calendar year must match the year in the start date."
			self._errors['calendar_year'] = self.error_class([msg])	
			del cleaned_data['calendar_year']


		return cleaned_data
