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
                  "VALUES ('site_creator', '*', 'AccountAdmin', '1'),"
                  "('site_creator', '*', 'Account Admin', '1'),"
                  "('site_creator', '*', 'Account admin', '1'),"
                  "('site_creator', '*', 'SchoolLiaison', '1');",
            reverse_sql="delete from lti_permissions_ltipermission where permission='site_creator';",
        ),
    ]

