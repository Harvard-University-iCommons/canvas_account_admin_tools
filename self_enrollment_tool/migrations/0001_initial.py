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
                  "VALUES ('self_enrollment_tool', '*', 'AccountAdmin', '1'),"
                  "('self_enrollment_tool', '*', 'Account admin', '1'),"
                  "('self_enrollment_tool', '*', 'Account Admin', '1'),"
                  "('self_enrollment_tool', '*', 'SchoolLiaison', '1');",
            reverse_sql="delete from lti_permissions_ltipermission where permission='self_enrollment_tool';",
        ),
    ]

