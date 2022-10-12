from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from core.endpoints import ACCOUNT_BALANCE
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
        parser.add_argument('balance')
        parser.add_argument('usage_percentage')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.balance = float(options['balance'])
        self.usage_percentage = (float(options['usage_percentage']))

        user = User.objects.get(telegram_id=self.telegram_id)
        if user.is_active:
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
                        available_balance = float(data['availableBalance'])

                if self.balance < available_balance * 2:
                    user.balance = self.balance
                    user.usage_percentage = self.usage_percentage
                    user.save()

                    self.stdout.write(
                        self.style.SUCCESS('User Balance Updated'))

                else:
                    self.stdout.write(self.style.ERROR(
                        'User Balance is more than Available Balance'))

            else:
                self.stdout.write(self.style.ERROR(
                    'User Credential is not Valid'))

        else:
            self.stdout.write(self.style.ERROR('User is not Active'))
