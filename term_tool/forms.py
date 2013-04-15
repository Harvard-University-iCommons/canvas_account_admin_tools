from datetime import date
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Fieldset, Submit, Button, HTML
from crispy_forms.bootstrap import FormActions

from icommons_common.models import Term,TermCode,School

import logging

logger = logging.getLogger(__name__)

class EditTermForm(forms.ModelForm):

    # this is a model form that's mostly automatically generated; here we specify that it should be based on the Term model:
    class Meta:
        model = Term

    # make the school, term_code and academic_year fields hidden; they should not be changed once the term is created
    school = forms.ModelChoiceField(queryset=School.objects.all(), widget=forms.widgets.HiddenInput())
    term_code = forms.ModelChoiceField(queryset=TermCode.objects.all(), widget=forms.widgets.HiddenInput())
    academic_year = forms.IntegerField(widget=forms.widgets.HiddenInput())
    source = forms.CharField(widget=forms.widgets.HiddenInput())

    hucc_academic_year = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput())

    # make the calendar_year hidden - it should not be directly editable (is determined based on start_date)
    calendar_year = forms.IntegerField(widget=forms.widgets.HiddenInput())

    # make some additional fields required; they're not strictly required in the database, but we want them to be required here
    start_date = forms.DateField(required=True)
    end_date = forms.DateField(required=True, help_text='The last day of the term, including exam period')
    xreg_start_date = forms.DateField(required=True, label='Cross-reg start date')
    xreg_end_date = forms.DateField(required=True, label='Cross-reg end date')

    active = forms.BooleanField(required=False,label='Active for Course iSites')

    include_in_catalog = forms.BooleanField(required=False,label='Include this term in the production Course Catalog')
    include_in_preview = forms.BooleanField(required=False,label='Include this term in the preview Course Catalog')

    enrollment_end_date = forms.DateField(required=False,help_text='The last day students can enroll in courses in this term')
    withdrawal_date = forms.DateField(required=False,help_text='The last day students can withdraw from courses in this term')
    
    def __init__(self, *args, **kwargs):
        super(EditTermForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.help_text_inline = True
        self.helper.error_text_inline = False
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            Field('academic_year'),
            Field('calendar_year'),
            Field('term_code'),
            Field('school'),
            Field('display_name'),
            Field('start_date'),
            Field('end_date'),
            Field('active'),
            Field('shopping_active'),
            Fieldset(
                'Cross-registration and Catalog',
                'xreg_start_date','xreg_end_date',
                'include_in_catalog','include_in_preview',
            ),
            Fieldset(
                'Other Dates',
                'enrollment_end_date',
                'drop_date',
                'withdrawal_date',
                'exam_start_date',
                'exam_end_date',
            ),

            FormActions(
                Submit('save','Save changes'),
                HTML('<a href="{% url "tt:termlist" school_id=object.school_id %}" class="btn btn-link">cancel</a>')
            ),
        )
    
    """
    override the clean method so that we can perform custom validation; this is done at the form level because some validation 
    rules depend on the values of multiple fields. 
    """
    def clean(self):

        cleaned_data = super(EditTermForm, self).clean()
        logger.debug("clean starting")
        school_id = cleaned_data.get('school')
        term_code = cleaned_data.get('term_code')
        academic_year = cleaned_data.get('academic_year')
        calendar_year = cleaned_data.get('calendar_year')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        xreg_start_date = cleaned_data.get('start_date')
        xreg_end_date = cleaned_data.get('end_date')
        display_name = cleaned_data.get('display_name')
        hucc_academic_year = cleaned_data.get('hucc_academic_year')

        # default the display_name if it's not set
        if display_name == None or display_name == '':
            cleaned_data['display_name'] = '{0} {1}'.format(term_code.term_name, academic_year)

        # make sure that the start date is before the end date
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("The start date must be before the end date.")

        # make sure that the xreg start date is before the xreg end date
        if xreg_start_date and xreg_end_date and xreg_start_date > xreg_end_date:
            raise forms.ValidationError("The cross-reg start date must be before the cross-reg end date.")

        # default the hucc_academic_year if it's not set (this field may go away someday)
        if hucc_academic_year == None or hucc_academic_year == '':
            cleaned_data['hucc_academic_year'] = academic_year

        # make sure that the xreg end date is between the term start and end
        if xreg_end_date > end_date or xreg_end_date < start_date:
            raise forms.ValidationError("The cross-reg end date must be between the term start and end dates.")

        # get the start date day-of-year
        start_day_of_year = start_date.timetuple()[7]

        # get the day-of-year for august 15th
        aug15_day_of_year = date(date.today().year,8,15).timetuple()[7]

        # the set of schools that use proper academic_year values for spring terms (not the calendar year)
        academic_year_schools = ['colgsas','ext','sum','hms','hsdm']

        # if the school is not colgsas,ext,sum,hms,hsdm then start date year must equal AY for all terms
        if school_id not in academic_year_schools:
            if academic_year != start_date.year:
                raise forms.ValidationError("The academic year of this term is %s. The start date of the term must be in that year." % academic_year) 

        # else if the term start date is between aug 15 and the end of the year, AY must equal start date year
        elif start_day_of_year >= aug15_day_of_year and academic_year != start_date.year:
            raise forms.ValidationError("The academic year of this term is %s.  For terms that take place during the Fall, the start date must be in that year." % academic_year)

        # else if the term start date is between the first of the year and Aug 15 start date year must equal AY+1
        elif start_day_of_year < aug15_day_of_year and start_date.year != academic_year+1:
            raise forms.ValidationError("The academic year of this term is %s. For terms that take place during the Winter, Spring or Summer, the start date must be in %s." % (academic_year, academic_year+1))
        
        # for all end dates, make sure the time portion is 11:59:59 PM
        # not sure if we should do this here or somewhere else...

        # make sure that the calendar_year matches the start_date
        
        if start_date and cleaned_data['calendar_year'] != start_date.year:
            logger.warn('setting the calendar year to %')
            cleaned_data['calendar_year'] = start_date.year
        

        """        
        if calendar_year and start_date and calendar_year != start_date.year:
            msg = u"The calendar year must match the year in the start date."
            self._errors['calendar_year'] = self.error_class([msg]) 
            del cleaned_data['calendar_year']
        """
        logger.debug("clean complete")
        #from pudb import set_trace; set_trace()

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
