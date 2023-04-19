# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('async_operations', '0002_process_created_by_user_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='status',
            field=models.CharField(default='', max_length=16, blank=True),
        ),
    ]
