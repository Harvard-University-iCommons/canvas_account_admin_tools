# Generated by Django 3.2.15 on 2022-10-20 05:54

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('self_enrollment_tool', '0004_populate_uuid_values'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selfenrollmentcourse',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]