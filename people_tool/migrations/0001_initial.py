# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

LTI_PERMISSIONS_DATA = [
    ('people_tool', '*', 'Account Observer', False),
    ('people_tool', '*', 'AccountAdmin', False),
    ('people_tool', '*', 'Account Admin', False),
    ('people_tool', '*', 'Course Head', False),
    ('people_tool', '*', 'Course Support Staff', False),
    ('people_tool', '*', 'Department Admin', False),
    ('people_tool', '*', 'DesignerEnrollment', False),
    ('people_tool', '*', 'Faculty', False),
    ('people_tool', '*', 'Guest', False),
    ('people_tool', '*', 'Harvard-Viewer', False),
    ('people_tool', '*', 'Help Desk', False),
    ('people_tool', '*', 'Librarian', False),
    ('people_tool', '*', 'ObserverEnrollment', False),
    ('people_tool', '*', 'SchoolLiaison', False),
    ('people_tool', '*', 'Prospective Enrollee', False),
    ('people_tool', '*', 'StudentEnrollment', False),
    ('people_tool', '*', 'TaEnrollment', False),
    ('people_tool', '*', 'TeacherEnrollment', False),
    ('people_tool', '*', 'Teaching Staff', False)
]


def create_lti_permissions(apps, schema_editor):
    LtiPermission = apps.get_model('lti_permissions', 'LtiPermission')
    fields = ('permission', 'school_id', 'canvas_role', 'allow')

    for permission in LTI_PERMISSIONS_DATA:
        LtiPermission.objects.create(**dict(zip(fields, permission)))


def reverse_permissions_load(apps, schema_editor):
    LtiPermission = apps.get_model('lti_permissions', 'LtiPermission')
    LtiPermission.objects.filter(permission='people_tool').delete()


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
