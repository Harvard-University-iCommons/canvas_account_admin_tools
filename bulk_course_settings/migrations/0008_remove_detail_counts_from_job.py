# Generated by Django 3.2.19 on 2024-02-02 21:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bulk_course_settings', '0007_modify_job_details_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='details_failed_count',
        ),
        migrations.RemoveField(
            model_name='job',
            name='details_skipped_count',
        ),
        migrations.RemoveField(
            model_name='job',
            name='details_success_count',
        ),
        migrations.RemoveField(
            model_name='job',
            name='details_total_count',
        ),
    ]