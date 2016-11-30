# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
         ('lti_permissions', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="INSERT INTO lti_permissions_ltipermission "
                  "(permission, school_id, canvas_role, allow) "
                  "VALUES ('manage_courses', '*', 'AccountAdmin', '1'),"
                  "('manage_courses', '*', 'Account Admin', '1'),"
                  "('manage_courses', '*', 'Account admin', '1'),"
                  "('manage_courses', '*', 'SchoolLiaison', '1');",
            reverse_sql="delete from lti_permissions_ltipermission where permission='manage_courses';",
        ),
    ]

