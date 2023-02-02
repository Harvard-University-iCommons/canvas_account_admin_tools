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
                  "VALUES ('bulk_site_creator', '*', 'AccountAdmin', '1'),"
                  "('bulk_site_creator', '*', 'Account Admin', '1'),"
                  "('bulk_site_creator', '*', 'Account admin', '1'),"
                  "('bulk_site_creator', '*', 'SchoolLiaison', '1');",
            reverse_sql="delete from lti_permissions_ltipermission where permission='bulk_site_creator';",
        ),
    ]

