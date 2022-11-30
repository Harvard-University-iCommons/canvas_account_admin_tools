from django.core.management.base import (BaseCommand, CommandError,
                                         CommandParser)
from django.db.utils import IntegrityError
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiToolKey, LtiTool



class Command(BaseCommand):
    help = "Generate a new LTI tool config and store in the database"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--key-name', type=str, required=True)
        parser.add_argument('--host', type=str, required=True, help='Typically this will be one of: canvas.instructure.com, canvas.beta.instructure.com or canvas.test.instructure.com')
        parser.add_argument('--client-id', type=str, required=True)

    def handle(self, *args, **options):
        key_name = options['key_name']
        host = options['host']
        client_id = options['client_id']

        key = LtiToolKey.objects.get(name=key_name)

        if key:
            tool_config = LtiTool(
                title=host,
                issuer=f'https://{host}',
                client_id=client_id,
                auth_login_url=f'https://{host}/api/lti/authorize_redirect',
                auth_token_url=f'https://{host}/login/oauth2/token',
                key_set_url=f'https://{host}/api/lti/security/jwks',
                deployment_ids=['unused'],
                tool_key=key,
            )
            try:
                tool_config.save()
            except IntegrityError as e:

                raise CommandError(f'Failed to save tool config: {e}') from e

            self.stdout.write(self.style.SUCCESS(f'Successfully created tool config for {host} and {client_id}!'))
        else:
            self.stdout.write(self.style.ERROR(f'Could not find a key with name "{key_name}"'))
