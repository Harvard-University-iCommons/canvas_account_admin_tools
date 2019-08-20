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
                  "VALUES ('canvas_site_deletion', '*', 'AccountAdmin', '1'),"
                  "('canvas_site_deletion', '*', 'Account admin', '1'),"
                  "('canvas_site_deletion', '*', 'Account Admin', '1');",
            reverse_sql="delete from lti_permissions_ltipermission where permission='cross_listing';",
        ),
    ]

