from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.settings import BINANCE_ENDPOINT
import json


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')
        parser.add_argument('symbol')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.symbol = options['symbol'].upper()

        try:
            user = User.objects.get(telegram_id=self.telegram_id)

            try:
                active_orders = session.get_active_order(
                    symbol=self.symbol)['result']['data']
                self.stdout.write(json.dumps(active_orders, indent=4))

            except InvalidRequestError:
                self.stdout.write(self.style.ERROR(
                    'User Credential is not Valid'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User Does Not Exist'))
