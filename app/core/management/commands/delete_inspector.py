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
            try:
                inspector = Inspector.objects.get(
                    user=user, code=self.inspector)
                inspector.delete()

                self.stdout.write(
                    self.style.SUCCESS('Inspector Deleted Successfully'))

            except Inspector.DoesNotExist:
                self.stderr.write('Inspector does not exist')

        except User.DoesNotExist:
            self.stderr.write('User does not exist')
