from django.db import models


class CanvasSchoolTemplate(models.Model):
    template_id = models.IntegerField()
    school_id = models.CharField(max_length=10, db_index=True)
    is_default = models.BooleanField(default=False)
    include_course_info = models.BooleanField(default=False)

    class Meta:
        app_label = 'canvas_account_admin_tools'
        db_table = 'canvas_school_template'

    def __unicode__(self):
        return f"(CanvasSchoolTemplate ID={self.pk}: school_id={self.school_id} | template_id={self.template_id}"
