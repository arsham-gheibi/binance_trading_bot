from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.endpoints import ACCOUNT_BALANCE
from core.utils import get_signiture
from urllib.parse import urlencode
import requests
import time
import json


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']

        try:
            user = User.objects.get(telegram_id=self.telegram_id)
            headers = {'X-MBX-APIKEY': user.api_key}
            params = {'timestamp': int(time.time() * 1000)}
            query_string = urlencode(params)
            params['signature'] = get_signiture(
                user.api_secret, query_string)

            res = requests.get(
                ACCOUNT_BALANCE,
                params=params,
                headers=headers
            )

            content = json.loads(res.content.decode('utf-8'))

            if res.status_code == 200:
                for data in content:
                    if data['asset'] == 'USDT':
                        equity = float(data['balance'])
                        available = float(data['availableBalance'])

            messages = [
                f'Used: {self.style.NOTICE(user.balance)}',
                f'Equity: {self.style.NOTICE(equity)}',
                f'Available: {self.style.NOTICE(available)}'
            ]

            for message in messages:
                self.stdout.write(self.style.SUCCESS(message))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'User Does Not Exist'))
