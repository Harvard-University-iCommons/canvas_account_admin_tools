# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-10 16:44


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulk_course_settings', '0003_auto_20180809_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='desired_setting',
            field=models.CharField(choices=[(b'True', b'True'), (b'False', b'False')], default=b'True', max_length=50),
        ),
    ]
