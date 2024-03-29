from django.db import models
from django.conf import settings

# Note: This model should go away along with a migration to delete the table,
# but due to some issues with unit tests failing on deletion of this model, they
# have been retained.

class ExternalToolManager(models.Manager):
    def get_external_tool_url_by_name_and_canvas_account_id(self, name, canvas_account_id):
        external_tool = None
        try:
            queryset = ExternalTool.objects.filter(name=name, canvas_account_id__in=[canvas_account_id, '*'])
            external_tools_by_canvas_account_id = {t.canvas_account_id: t for t in queryset}
            if canvas_account_id in external_tools_by_canvas_account_id:
                external_tool = external_tools_by_canvas_account_id[canvas_account_id]
            elif '*' in external_tools_by_canvas_account_id:
                external_tool = external_tools_by_canvas_account_id['*']
        except ExternalTool.DoesNotExist:
            pass

        external_tool_url = None
        if external_tool:
            external_tool_url = "%s/accounts/%s/external_tools/%s" % (
                settings.CANVAS_URL,
                canvas_account_id,
                external_tool.external_tool_id
            )
        return external_tool_url


class ExternalTool(models.Model):
    CANVAS_SITE_CREATOR = 'canvas_site_creator'
    LTI_TOOLS_USAGE = 'lti_tools_usage'
    COURSES_IN_THIS_ACCOUNT = 'courses_in_this_account'
    NAME_CHOICES = (
        (CANVAS_SITE_CREATOR, 'Canvas Site Creator'),
        (LTI_TOOLS_USAGE, 'LTI Tools Usage'),
        (COURSES_IN_THIS_ACCOUNT, 'Courses in this account'),
    )

    name = models.CharField(max_length=32, choices=NAME_CHOICES)
    canvas_account_id = models.CharField(max_length=8, default='*')
    canvas_course_id = models.CharField(max_length=8, default='*')
    external_tool_id = models.IntegerField()

    objects = ExternalToolManager()


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
