# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalTool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, choices=[(b'canvas_site_creator', b'Canvas Site Creator'), (b'lti_tools_usage', b'LTI Tools Usage'), (b'courses_in_this_account', b'Courses in this account')])),
                ('canvas_account_id', models.CharField(default=b'*', max_length=8)),
                ('canvas_course_id', models.CharField(default=b'*', max_length=8)),
                ('external_tool_id', models.IntegerField()),
            ],
        ),
    ]
