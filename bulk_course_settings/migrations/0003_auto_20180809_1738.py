# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-09 21:38


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulk_course_settings', '0002_add_bulk_course_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='setting_to_be_modified',
            field=models.CharField(choices=[(b'is_public', b'Course is public'), (b'is_public_to_auth_users', b'Course is public to auth users'), (b'public_syllabus', b'Public syllabus'), (b'public_syllabus_to_auth', b'Syllabus is public to auth users')], default=b'is_public', max_length=50),
        ),
    ]
