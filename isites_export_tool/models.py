from django.db import models

class ISitesExportJob(models.Model):
    # Job status values
    STATUS_NEW = 'New'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_ERROR = 'Error'
    STATUS_COMPLETE = 'Complete'
    # Job status choices
    JOB_STATUS_CHOICES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_IN_PROGRESS, STATUS_IN_PROGRESS),
        (STATUS_ERROR, STATUS_ERROR),
        (STATUS_COMPLETE, STATUS_COMPLETE)
    )
    # Fields
    created_by = models.CharField(max_length=30)
    created_on = models.DateField(auto_now_add=True)
    site_keyword = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=JOB_STATUS_CHOICES, default=STATUS_NEW)
    archived_on = models.DateField(null=True, blank=True)
    output_file_name = models.CharField(max_length=100, blank=True)
    output_message = models.CharField(max_length=250, blank=True)

    class Meta:
        db_table = u'isites_export_job'
        
    def __unicode__(self):
        return self.site_keyword + " | " + self.status
