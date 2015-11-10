# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import isites_export_tool.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ISitesExportJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_by', models.CharField(default=None, max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('site_keyword', models.CharField(max_length=30, validators=[isites_export_tool.models.validate_site_exists])),
                ('status', models.CharField(default=b'New', max_length=15, choices=[(b'New', b'New'), (b'In Progress', b'In Progress'), (b'Error', b'Error'), (b'Complete', b'Complete'), (b'Archived', b'Archived')])),
                ('archived_on', models.DateField(null=True, blank=True)),
                ('output_file_name', models.CharField(max_length=100, blank=True)),
                ('output_message', models.CharField(max_length=250, blank=True)),
            ],
            options={
                'db_table': 'isites_export_job',
            },
        ),
    ]
