from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from core.endpoints import POSITIONS
from core.utils import get_signiture
from urllib.parse import urlencode
import requests
import time
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
            headers = {'X-MBX-APIKEY': user.api_key}
            params = {'timestamp': int(time.time() * 1000)}

            if self.symbol == 'ALL':
                all_positions = []
                query_string = urlencode(params)
                params['signature'] = get_signiture(
                    user.api_secret, query_string)

                res = requests.get(
                    POSITIONS,
                    params=params,
                    headers=headers
                )

                positions = json.loads(res.content.decode('utf-8'))

                for position in positions:
                    if float(position['entryPrice']) != 0:
                        all_positions.append(position)

                positions = all_positions

            else:
                params['symbol'] = self.symbol
                query_string = urlencode(params)
                params['signature'] = get_signiture(
                    user.api_secret, query_string)

                res = requests.get(
                    POSITIONS,
                    params=params,
                    headers=headers
                )

                positions = json.loads(res.content.decode('utf-8'))

            if res.status_code == 200:
                self.stdout.write(json.dumps(positions, indent=4))

            else:
                self.stdout.write(self.style.ERROR(
                    'User Credential is not Valid'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User Does Not Exist'))
