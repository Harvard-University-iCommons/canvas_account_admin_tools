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
    source = forms.CharField(required=False, widget=forms.widgets.HiddenInput())

    hucc_academic_year = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput())

    # make the calendar_year hidden - it should not be directly editable (is determined based on start_date)
    calendar_year = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput())

    # hide user_id and modified_on fields, they should not be directlty editable
    user_id = forms.CharField(required=False, widget=forms.widgets.HiddenInput())
    modified_on = forms.DateField(required=False, widget=forms.widgets.HiddenInput())

    # make some additional fields required; they're not strictly required in the database, but we want them to be required here
    start_date = forms.DateField(required=True)
    end_date = forms.DateField(required=True, help_text='The last day of the term, including exam period')
    xreg_start_date = forms.DateField(required=True, label='Cross-reg start date')
    xreg_end_date = forms.DateField(required=True, label='Cross-reg end date')

    active = forms.BooleanField(required=False,label='Active for Course iSites')
    shopping_active = forms.BooleanField(required=False)

    include_in_catalog = forms.BooleanField(required=False,label='Include this term in the production Course Catalog')
    include_in_preview = forms.BooleanField(required=False,label='Include this term in the preview Course Catalog')

    enrollment_end_date = forms.DateField(required=False,help_text='The last day students can enroll in courses in this term')
    withdrawal_date = forms.DateField(required=False,help_text='The last day students can withdraw from courses in this term')
    shopping_end_date = forms.DateField(required=False)
    
    def __init__(self, *args, **kwargs):
        super(EditTermForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.help_text_inline = True
        self.helper.form_class = 'form-horizontal'
        self.helper.render_unmentioned_fields = True
        self.helper.form_error_title = u"There were problems with the information you submitted."        
        self.helper.layout = Layout(
            Field('academic_year'),
            Field('calendar_year'),
            Field('hucc_academic_year'),
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
                'shopping_end_date',
                'enrollment_end_date',
                'drop_date',
                'withdrawal_date',
                'exam_start_date',
                'exam_end_date',
            ),
            Field('user_id'),
            Field('modified_on'),
            FormActions(
                Submit('save','Save changes'),
            ),
        )

#                HTML('<a href="{% url "tt:termlist" school_id=object.school_id %}" class="btn btn-link">cancel</a>')
    
    """
    override the clean method so that we can perform custom validation; this is done at the form level because some validation 
    rules depend on the values of multiple fields. 
    """
    def clean(self):

        cleaned_data = super(EditTermForm, self).clean()
        logger.debug("clean starting")
        school = cleaned_data.get('school')
        term_code = cleaned_data.get('term_code')
        academic_year = cleaned_data.get('academic_year')
        calendar_year = cleaned_data.get('calendar_year')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        xreg_start_date = cleaned_data.get('xreg_start_date')
        xreg_end_date = cleaned_data.get('xreg_end_date')
        display_name = cleaned_data.get('display_name')
        hucc_academic_year = cleaned_data.get('hucc_academic_year')
        shopping_end_date = cleaned_data.get('shopping_end_date')
        enrollment_end_date = cleaned_data.get('enrollment_end_date')
        drop_date = cleaned_data.get('drop_date')
        withdrawal_date = cleaned_data.get('withdrawal_date')
        exam_start_date = cleaned_data.get('exam_start_date')
        exam_end_date = cleaned_data.get('exam_end_date')
        source = cleaned_data.get('source')
        user_id = cleaned_data.get('user_id')
        modified_on = cleaned_data.get('modified_on')

        logger.debug(">>>>>> IN CLEAN DATA")
        logger.debug(user_id)
        logger.debug(modified_on)

        # default the display_name if it's not set
        if display_name == None or display_name == '':
            cleaned_data['display_name'] = '{0} {1}'.format(term_code.term_name, academic_year)

        # make sure that the start date is before the end date
        if start_date and end_date and start_date > end_date:
            self._errors['start_date'] = self.error_class(['']) 
            self._errors['end_date'] = self.error_class(['']) 
            raise forms.ValidationError("The start date must be before the end date.")

        
        # make sure that the interval between the start date and end date is less than one year
        if start_date and end_date and (end_date.toordinal() - start_date.toordinal()) > 365:
            self._errors['start_date'] = self.error_class(['']) 
            self._errors['end_date'] = self.error_class(['']) 
            raise forms.ValidationError("The start date and end date cannot be more than one year apart.")
        
        # make sure that the xreg start date is before the xreg end date
        if xreg_start_date and xreg_end_date and xreg_start_date > xreg_end_date:
            self._errors['xreg_start_date'] = self.error_class(['']) 
            self._errors['xreg_end_date'] = self.error_class(['']) 
            raise forms.ValidationError("The cross-reg start date must be before the cross-reg end date.")

        
        # make sure that the interval between the xreg_start date and xreg_end date is less than one year
        if xreg_start_date and xreg_end_date and (xreg_end_date.toordinal() - xreg_start_date.toordinal()) > 365:
            logger.warn("xreg_interval too greater than one year")
            self._errors['xreg_start_date'] = self.error_class(['']) 
            self._errors['xreg_end_date'] = self.error_class(['']) 
            raise forms.ValidationError("The cross-registration start date and end date cannot be more than one year apart.")
        
        # default the hucc_academic_year if it's not set (this field may go away someday)
        if hucc_academic_year == None or hucc_academic_year == '':
            logger.warn('setting the hucc_academic_year to %s' % academic_year)
            cleaned_data['hucc_academic_year'] = academic_year

        # set the source if it's not already set
        if source == None or source == '':
            logger.warn('setting the source')
            cleaned_data['source'] = 'termtool'

        # make sure that the xreg end date is between the term start and end
        if xreg_end_date > end_date or xreg_end_date < start_date:
            logger.warn("xreg_end_date outside of term start/end")
            self._errors['xreg_start_date'] = self.error_class(['']) 
            raise forms.ValidationError("The cross-reg end date must be between the term start and end dates.")

        # get the start date day-of-year
        start_day_of_year = start_date.timetuple()[7]

        # get the day-of-year for august 15th
        aug15_day_of_year = date(date.today().year,8,15).timetuple()[7]

        logger.debug('start_day_of_year / aug15 day of year: %s / %s' % (start_day_of_year,aug15_day_of_year))

        # the set of schools that use proper academic_year values for spring terms (not the calendar year)
        academic_year_schools = ['colgsas','ext','sum','hms','hsdm']

        # if the school is not colgsas,ext,sum,hms,hsdm then start date year must equal AY for all terms
        if school.school_id not in academic_year_schools:
            logger.debug('school %s is not in the list of schools that use a proper academic year' % school.school_id)
            if academic_year != start_date.year:
                self._errors['start_date'] = self.error_class(['']) 
                raise forms.ValidationError("The academic year of this term is %s. The start date of the term must be in that year." % academic_year) 

        # else if the term start date is between aug 15 and the end of the year, AY must equal start date year
        elif start_day_of_year >= aug15_day_of_year and academic_year != start_date.year:
            self._errors['start_date'] = self.error_class(["The start date must be in %s." % academic_year]) 
            raise forms.ValidationError("The academic year of this term is %s.  For terms that take place during the Fall, the start date must be in that year." % academic_year)

        # else if the term start date is between the first of the year and Aug 15 start date year must equal AY+1
        elif start_day_of_year < aug15_day_of_year and start_date.year != academic_year+1:
            self._errors['start_date'] = self.error_class(["The start date must be in %s." % academic_year+1]) 
            raise forms.ValidationError("The academic year of this term is %s. For terms that take place during the Winter, Spring or Summer, the start date must be in %s." % (academic_year, academic_year+1))
        
        # for all end dates, make sure the time portion is 11:59:59 PM
        # not sure if we should do this here or somewhere else...

        # make sure that the calendar_year matches the start_date
        
        if start_date and cleaned_data['calendar_year'] != start_date.year:
            logger.warn('setting the calendar year to %s' % start_date.year)
            cleaned_data['calendar_year'] = start_date.year
        

        if shopping_end_date and (shopping_end_date < start_date or shopping_end_date > end_date):
            msg = u"The shopping end date, if provided, must fall between the term start and end dates."
            self._errors['shopping_end_date'] = self.error_class([msg]) 
            del cleaned_data['shopping_end_date']
            raise forms.ValidationError(msg) 

        if enrollment_end_date and (enrollment_end_date < start_date or enrollment_end_date > end_date):
            msg = u"The enrollment end date, if provided, must fall between the term start and end dates."
            self._errors['enrollment_end_date'] = self.error_class([msg]) 
            del cleaned_data['enrollment_end_date']
            raise forms.ValidationError(msg) 

        if drop_date and (drop_date < start_date or drop_date > end_date):
            msg = u"The drop date, if provided, must fall between the term start and end dates."
            self._errors['drop_date'] = self.error_class([msg]) 
            del cleaned_data['drop_date']
            raise forms.ValidationError(msg) 

        if withdrawal_date and (withdrawal_date < start_date or withdrawal_date > end_date):
            msg = u"The withdrawal date, if provided, must fall between the term start and end dates."
            self._errors['withdrawal_date'] = self.error_class([msg]) 
            del cleaned_data['withdrawal_date']
            raise forms.ValidationError(msg) 

        if exam_start_date and (exam_start_date < start_date or exam_start_date > end_date):
            msg = u"The exam start date, if provided, must fall between the term start and end dates."
            self._errors['exam_start_date'] = self.error_class([msg]) 
            del cleaned_data['exam_start_date']
            raise forms.ValidationError(msg) 

        if exam_end_date and (exam_end_date < start_date or exam_end_date > end_date):
            msg = u"The exam end date, if provided, must fall between the term start and end dates."
            self._errors['exam_end_date'] = self.error_class([msg]) 
            del cleaned_data['exam_end_date']
            raise forms.ValidationError(msg) 

        """        
        if calendar_year and start_date and calendar_year != start_date.year:
            msg = u"The calendar year must match the year in the start date."
            self._errors['calendar_year'] = self.error_class([msg]) 
            del cleaned_data['calendar_year']
        """
        logger.debug("clean complete")
        logger.debug(cleaned_data)
        #from pudb import set_trace; set_trace()

        return cleaned_data


# the Create form is just like the edit form except that the academic year and term code are not hidden,
# and there are some additional validation rules

class CreateTermForm(EditTermForm):

    term_code = forms.ModelChoiceField(required=True, queryset=TermCode.objects.all())
    academic_year = forms.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(CreateTermForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.help_text_inline = True
        self.helper.form_class = 'form-horizontal'
        self.helper.render_unmentioned_fields = True
        self.helper.form_error_title = u"There were problems with the information you submitted."        
        self.helper.layout = Layout(
            Field('academic_year'),
            Field('calendar_year'),
            Field('hucc_academic_year'),
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
                'shopping_end_date',
                'enrollment_end_date',
                'drop_date',
                'withdrawal_date',
                'exam_start_date',
                'exam_end_date',
            ),
            FormActions(
                Submit('save','Save changes'),
            ),
        )

    def clean(self):

        cleaned_data = super(CreateTermForm, self).clean()

        # make sure that there isn't already a term with this school/ac year/term code combination
        

        # make sure that there isn't already a term with this school/cal year/term code combination


        return cleaned_data        
        school = cleaned_data.get('school')
        term_code = cleaned_data.get('term_code')
        academic_year = cleaned_data.get('academic_year')
        calendar_year = cleaned_data.get('calendar_year')    


class xCreateTermForm(forms.ModelForm):

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
