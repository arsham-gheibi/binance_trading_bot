from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import json


User = get_user_model()
BINANCE_ENDPOINT = settings.BINANCE_ENDPOINT


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
                if self.symbol == 'ALL':
                    all_positions = []
                    positions = session.my_position()['result']
                    for position in positions:
                        data = position['data']
                        if data['side'] in ('Buy', 'Sell'):
                            all_positions.append(data)
                    positions = all_positions

                else:
                    positions = session.my_position(
                        symbol=self.symbol)['result']

                self.stdout.write(json.dumps(positions, indent=4))

            except InvalidRequestError:
                self.stdout.write(self.style.ERROR(
                    'User Credential is not Valid'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User Does Not Exist'))
