# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import itertools

from django.conf import settings
from django.db import migrations

from lti_permissions.models import DEFAULT_ROLES, DEFAULT_SCHOOLS


# intialize permissions for all apps to the defaults (TLT-2650)
PERMISSION_NAMES = settings.TOOL_PERMISSIONS.values()
SCHOOL_PERMISSION_DATA = itertools.product(
    PERMISSION_NAMES,
    DEFAULT_SCHOOLS,
    DEFAULT_ROLES)


def create_school_permissions(apps, schema_editor):
    SchoolPermission = apps.get_model('lti_permissions', 'SchoolPermission')
    fields = ('permission', 'school_id', 'canvas_role')

    for permission in SCHOOL_PERMISSION_DATA:
        SchoolPermission.objects.create(**dict(zip(fields, permission)))


def reverse_permissions_load(apps, schema_editor):
    SchoolPermission = apps.get_model('lti_permissions', 'SchoolPermission')
    SchoolPermission.objects.filter(permission__in=PERMISSION_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('canvas_account_admin_tools', '0001_initial'),
        ('lti_permissions', '0002_schoolpermission_20160826_0039'),
    ]

    operations = [
        migrations.RunPython(
            code=create_school_permissions,
            reverse_code=reverse_permissions_load,
        ),
    ]
