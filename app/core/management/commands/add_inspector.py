from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import Inspector


User = get_user_model()
BINANCE_ENDPOINT = settings.BINANCE_ENDPOINT


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')
        parser.add_argument('inspector')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.inspector = options['inspector']

        try:
            user = User.objects.get(telegram_id=self.telegram_id)
            Inspector.objects.create(user=user, code=self.inspector)
            self.stdout.write(
                self.style.SUCCESS('Inspector successfully created'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User does not exist'))
