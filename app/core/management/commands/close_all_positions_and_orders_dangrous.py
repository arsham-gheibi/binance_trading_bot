from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.endpoints import ORDER_ENDPOINT, CANCEL_OPEN_ORDERS, POSITIONS
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
            params['signature'] = get_signiture(user.api_secret, query_string)
            res = requests.get(
                POSITIONS,
                params=params,
                headers=headers
            )

            positions = json.loads(res.content.decode('utf-8'))
            for position in positions:
                entry_price = float(position['entryPrice'])
                if entry_price > 0:
                    symbol = position['symbol']
                    quantity = float(position['positionAmt'])
                    position_side = position['positionSide']

                    if quantity > 0:
                        side = 'SELL'
                    elif quantity < 0:
                        side = 'BUY'

                    params = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'MARKET',
                        'positionSide': position_side,
                        'quantity': abs(quantity),
                        'reduceOnly': True,
                        'timestamp': int(time.time() * 1000)
                    }

                    query_string = urlencode(params)
                    params['signature'] = get_signiture(
                        user.api_secret, query_string
                    )

                    res = requests.post(
                        ORDER_ENDPOINT,
                        params=params,
                        headers=headers
                    )

                    content = json.loads(res.content.decode('utf-8'))

                    try:
                        content['status']
                        content['orderId']
                        self.stdout.write(self.style.SUCCESS('Order Closed'))

                    except KeyError:
                        print("Order Didn't Close")

                    params = {
                        'symbol': symbol,
                        'timestamp': int(time.time() * 1000)
                    }

                    query_string = urlencode(params)
                    params['signature'] = get_signiture(
                        user.api_secret, query_string
                    )

                    res = requests.delete(
                        CANCEL_OPEN_ORDERS,
                        params=params,
                        headers=headers
                    )

                    if res.status_code == 200:
                        self.stdout.write(
                            self.style.SUCCESS('All Active Orders Cancelled'))
                    else:
                        self.stderr.write(
                            'There is no Active Order with this symbol')

                else:
                    self.stderr.write('Position does not exist')

        except User.DoesNotExist:
            self.stderr.write('User Does Not Exist')
