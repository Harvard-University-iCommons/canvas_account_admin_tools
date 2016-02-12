# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def load_data(apps, schema_editor):
    LtiPermissionsPerm = apps.get_model("cross_list_courses", "lti_permissions_ltipermission")

    LtiPermissionsPerm('cross_listing',
                       'AccountAdmin', '*',True).save()


class Migration(migrations.Migration):
    print("\n\n---------------")
    print(migrations.Migration)

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(
            # sql='INSERT INTO lti_permissions_ltipermission (permission, school_id, canvas_role, allow) VALUES("cross_listing", "*", "Account Observer", FALSE)',
            sql = "INSERT INTO lti_permissions_ltipermission "
                  "(permission, school_id, canvas_role, allow) "
                  "VALUES ('cross_listing', '*', 'AccountAdmin', TRUE),"
                  "('cross_listing', '*', 'Account Admin', TRUE);",
            reverse_sql='delete  from lti_permissions_ltipermission where permission="cross_listing"',
        ),
    ]






            # migrations.RunSQL('INSERT INTO lti_permissions_ltipermission values ("cross_listing", "*", "Account Observer", FALSE)')
            # sql='UPDATE school_allowed_role SET user_role_id=temp_user_role_id',

  # migrations.RunPython(load_data)
  #       migrations.RunSQL(sql)
        # migrations.RunSQL("INSERT INTO lti_permissions_ltipermission (permission, school_id, canvas_role, allow) VALUES 	('cross_listing', '*', 'Account Observer', FALSE), 	('cross_listing', '*', 'AccountAdmin', TRUE), 	('cross_listing', '*', 'Account Admin', TRUE), 	('cross_listing', '*', 'Course Head', FALSE), 	('cross_listing', '*', 'Course Support Staff', FALSE), 	('cross_listing', '*', 'Department Admin', FALSE), 	('cross_listing', '*', 'DesignerEnrollment', FALSE), 	('cross_listing', '*', 'Faculty', FALSE), 	('cross_listing', '*', 'Guest', FALSE), 	('cross_listing', '*', 'Harvard-Viewer', FALSE), 	('cross_listing', '*', 'Help Desk', FALSE), 	('cross_listing', '*', 'Librarian', FALSE), 	('cross_listing', '*', 'ObserverEnrollment', FALSE), 	('cross_listing', '*', 'SchoolLiaison', FALSE), 	('cross_listing', '*', 'Shopper', FALSE), 	('cross_listing', '*', 'StudentEnrollment', FALSE), 	('cross_listing', '*', 'TaEnrollment', FALSE), 	('cross_listing', '*', 'TeacherEnrollment', FALSE), 	('cross_listing', '*', 'Teaching Staff', FALSE) ")
