# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
         ('lti_permissions', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="INSERT INTO lti_permissions_ltipermission "
                  "(permission, school_id, canvas_role, allow) "
                  "VALUES ('masquerade_tool', '*', 'Account Admin', '1'),"
                  "('masquerade_tool', '*', 'AccountAdmin', '1'),"
                  "('masquerade_tool', '*', 'SchoolLiaison', '1'),"
                  "('masquerade_tool', '*', 'School Liaison', '1');",
            reverse_sql="delete from lti_permissions_ltipermission where permission='masquerade_tool';",
        ),
    ]

