from django.db import models
from icommons_common.models import Person, Site
from django.forms import ModelForm, ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from django.utils.functional import cached_property


def validate_site_exists(keyword):
    if (Site.objects.filter(keyword=keyword).count() == 0):
        raise ValidationError(u'keyword does not map to an existing iSite!')


class ISitesExportJob(models.Model):
    # Job status values
    STATUS_NEW = 'New'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_ERROR = 'Error'
    STATUS_COMPLETE = 'Complete'
    STATUS_ARCHIVED = 'Archived'
    # Job status choices
    JOB_STATUS_CHOICES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
        (STATUS_ERROR, STATUS_ERROR),
        (STATUS_COMPLETE, STATUS_COMPLETE),
        (STATUS_ARCHIVED, STATUS_ARCHIVED),
    )
    ############
    # Fields
    ############
    # defaulting created_at to None to force validation to require a value -
    # default is '' which Django thinks is fine!
    created_by = models.CharField(max_length=30, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    site_keyword = models.CharField(max_length=30, validators=[validate_site_exists])
    status = models.CharField(max_length=15, choices=JOB_STATUS_CHOICES, default=STATUS_NEW)
    archived_on = models.DateField(null=True, blank=True)
    output_file_name = models.CharField(null=True, max_length=100, blank=True)
    output_message = models.CharField(null=True, max_length=250, blank=True)

    class Meta:
        db_table = u'isites_export_job'

    def __unicode__(self):
        return self.site_keyword + " | " + self.status

    def is_complete(self):
        return self.status == ISitesExportJob.STATUS_COMPLETE

    @cached_property
    def person(self):
        return Person.objects.filter(univ_id=self.created_by)[0]


class ISitesExportJobForm(ModelForm):

    def __init__(self, request=None, *args, **kwargs):
        super(ISitesExportJobForm, self).__init__(*args, **kwargs)
        self.request = request
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline col-sm-8'
        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            Field('site_keyword', placeholder='Enter a site keyword to archive...'),
            Submit('export', 'Export', css_class='btn_default'),
        )

    # Trick lifted from stack overflow to also save the created_by based on the currently logged in user...
    def save(self, *args, **kwargs):
        kwargs['commit'] = False  # Don't want to save the model twice
        obj = super(ISitesExportJobForm, self).save(*args, **kwargs)
        if self.request:
            obj.created_by = self.request.user.username  # Username is equivalent to univ_id
        obj.save()
        return obj  # Return saved object to caller.

    class Meta:
        model = ISitesExportJob
        fields = ['site_keyword']
