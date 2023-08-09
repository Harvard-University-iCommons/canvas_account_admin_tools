# -*- coding: utf-8 -*-

from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    # Removed dependency on (deleted) migration file 0001_initial.py because that migration
    # file was used to manipulate school permissions for the tool in older lti permission 
    # tables in the database. And the 0001_initial.py file also had dependency on older
    # lti permission library. We now use the django-canvas-lti-school-permissions library
    # and we have created new permission tables (lti_school_permission) in the database.
    # Note: The deleted 0001_initial.py file migration record in the database may also be deleted.
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SelfEnrollmentCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_instance_id', models.IntegerField(blank=True, null=True)),
                ('role_id', models.CharField(blank=True, max_length=20, null=True)),
                ('updated_by', models.CharField(max_length=15)),
                ('last_updated', models.DateTimeField(auto_now_add=True)),
            ],
        )
    ]
