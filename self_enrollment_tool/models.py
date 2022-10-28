from django.db import models


class SelfEnrollmentCourse(models.Model):

    course_instance_id = models.IntegerField(unique=True)
    role_id = models.IntegerField()
    updated_by = models.CharField(max_length=15)
    last_updated = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'self_enrollment_course'
        