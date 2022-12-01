from django.core.management.base import (BaseCommand, CommandError,
                                         CommandParser)
from django.db.utils import IntegrityError
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiToolKey



class Command(BaseCommand):
    help = "List the existing LTI tool keys in the database"

    def handle(self, *args, **options):
        keys = LtiToolKey.objects.all()

        self.stdout.write('Key names:')
        for k in keys:
            self.stdout.write(f'\t"{k.name}"')
