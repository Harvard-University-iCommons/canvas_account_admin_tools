# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
from django.contrib.postgres.fields import JSONField


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('source', models.CharField(max_length=128)),
                ('state', models.CharField(default=b'queued', max_length=16, choices=[(b'queued', b'Queued'), (b'active', b'Active'), (b'complete', b'Complete')])),
                ('status', models.CharField(max_length=16, null=True, blank=True)),
                ('details', JSONField(null=True, blank=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('date_active', models.DateTimeField(null=True, blank=True)),
                ('date_complete', models.DateTimeField(null=True, blank=True)),
            ],
        ),
    ]
