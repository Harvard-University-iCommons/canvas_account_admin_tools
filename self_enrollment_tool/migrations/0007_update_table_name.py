# Generated by Django 3.2.15 on 2022-10-28 19:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('self_enrollment_tool', '0006_add_unique_together_constraint'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='selfenrollmentcourse',
            table='self_enrollment_course',
        ),
    ]
