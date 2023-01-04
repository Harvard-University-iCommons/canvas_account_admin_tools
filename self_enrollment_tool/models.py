from django.db import models
from uuid import uuid4


class SelfEnrollmentCourse(models.Model):

    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    uuid = models.UUIDField(default=uuid4, unique=True)
    course_instance_id = models.IntegerField()
    role_id = models.CharField(max_length=20)
    updated_by = models.CharField(max_length=15)
    last_updated = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course_instance_id', 'role_id',)
        db_table = 'self_enrollment_course'
