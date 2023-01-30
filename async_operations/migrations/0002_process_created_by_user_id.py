# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('async_operations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='process',
            name='created_by_user_id',
            field=models.CharField(max_length=20, blank=True),
        ),
    ]
