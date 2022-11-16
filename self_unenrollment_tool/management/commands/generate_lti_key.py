import json

from Crypto.PublicKey import RSA
from django.core.management.base import (BaseCommand, CommandError,
                                         CommandParser)
from django.db.utils import IntegrityError
from jwcrypto.jwk import JWK
from pylti1p3.contrib.django.lti1p3_tool_config.models import LtiToolKey


class Command(BaseCommand):
    help = "Generate a new LTI tool key pair"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('name', type=str)

    def handle(self, *args, **options):

        key = RSA.generate(4096)
        private_key = key.exportKey().decode('utf-8')
        public_key = key.publickey().exportKey().decode('utf-8')
        name = options['name']
        tool_key = LtiToolKey(
            name=name,
            private_key=private_key,
            public_key=public_key
        )
        try:
            tool_key.save()
        except IntegrityError as e:
            raise CommandError(f'Failed to save tool key: another key with the name "{name}" already exists') from e

        self.stdout.write(self.style.SUCCESS(f'Successfully created key "{name}"!'))
