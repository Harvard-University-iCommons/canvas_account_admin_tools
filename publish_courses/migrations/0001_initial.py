# -*- coding: utf-8 -*-


from django.db import migrations

LTI_PERMISSIONS_DATA = [
    ('publish_courses', '*', 'Account Admin', True),
    ('publish_courses', '*', 'SchoolLiaison', True),
]

def create_lti_permissions(apps, schema_editor):
    LtiPermission = apps.get_model('lti_permissions', 'LtiPermission')
    fields = ('permission', 'school_id', 'canvas_role', 'allow')

    for permission in LTI_PERMISSIONS_DATA:
        LtiPermission.objects.create(**dict(list(zip(fields, permission))))


def reverse_permissions_load(apps, schema_editor):
    LtiPermission = apps.get_model('lti_permissions', 'LtiPermission')
    LtiPermission.objects.filter(permission='publish_courses').delete()


class Migration(migrations.Migration):

    dependencies = [
         ('lti_permissions', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            code=create_lti_permissions,
            reverse_code=reverse_permissions_load,
        ),
    ]
