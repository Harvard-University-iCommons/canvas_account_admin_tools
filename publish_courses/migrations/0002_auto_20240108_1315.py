# Generated by Django 3.2.20 on 2024-01-08 18:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publish_courses', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='job_details_failed_count',
        ),
        migrations.RemoveField(
            model_name='job',
            name='job_details_total_count',
        ),
        migrations.RemoveField(
            model_name='jobdetails',
            name='prior_state',
        ),
    ]
