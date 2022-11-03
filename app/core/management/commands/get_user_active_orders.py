from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.endpoints import OPEN_ORDERS
from core.utils import get_signiture
from urllib.parse import urlencode
import requests
import time
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
            headers = {'X-MBX-APIKEY': user.api_key}
            params = {'timestamp': int(time.time() * 1000)}

            if self.symbol == 'ALL':
                query_string = urlencode(params)
                params['signature'] = get_signiture(
                    user.api_secret, query_string)

                res = requests.get(
                    OPEN_ORDERS,
                    params=params,
                    headers=headers
                )

            else:
                params['symbol'] = self.symbol
                query_string = urlencode(params)
                params['signature'] = get_signiture(
                    user.api_secret, query_string)

                res = requests.get(
                    OPEN_ORDERS,
                    params=params,
                    headers=headers
                )

            if res.status_code == 200:
                content = json.loads(res.content.decode('utf-8'))
                self.stdout.write(json.dumps(content, indent=4))

            else:
                self.stderr.write('User Credential is not Valid')

        except User.DoesNotExist:
            self.stderr.write('User Does Not Exist')
