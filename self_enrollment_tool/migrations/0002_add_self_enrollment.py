# -*- coding: utf-8 -*-

from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

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
