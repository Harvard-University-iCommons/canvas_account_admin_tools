from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.management.base import (BaseCommand, CommandError,
                                         CommandParser)
from django.db.utils import IntegrityError
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiToolKey


class Command(BaseCommand):
    help = "Generate a new LTI tool key pair and store in the database"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('name', type=str)

    def handle(self, *args, **options):

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        name = options['name']
        tool_key = LtiToolKey(
            name=name,
            private_key=private_key.decode('utf-8'),
            public_key=public_key.decode('utf-8')
        )
        try:
            tool_key.save()
        except IntegrityError as e:
            raise CommandError(f'Failed to save tool key: another key with the name "{name}" already exists') from e

        self.stdout.write(self.style.SUCCESS(f'Successfully created key "{name}"!'))
