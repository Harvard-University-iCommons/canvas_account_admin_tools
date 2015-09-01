from django.db import models


class SelfregCourse(models.Model):
    canvas_course_id = models.IntegerField(unique=True)
    canvas_role_name = models.CharField(max_length=32)
