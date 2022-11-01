from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from app.celery import celery_app
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
        parser.add_argument('api_key')
        parser.add_argument('api_secret')
        parser.add_argument('balance')
        parser.add_argument('usage_percentage')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.api_key = options['api_key']
        self.api_secret = options['api_secret']
        self.balance = float(options['balance'])
        self.usage_percentage = (float(options['usage_percentage']))

        try:
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
                            equity = float(data['balance'])

                    if self.balance < equity * 2:
                        user.api_key = self.api_key
                        user.api_secret = self.api_secret
                        user.balance = self.balance
                        user.usage_percentage = self.usage_percentage
                        user.save()

                        task_id = cache.get(user.id)
                        celery_app.control.terminate(task_id)

                        stream_task = celery_app.send_task(
                            'core.tasks.user_data_stream',
                            [user.id],
                            time_limit=31536000,
                            soft_time_limit=31536000,
                            queue=user.stream_queue.name)

                        cache.set(user.id, stream_task.task_id, 31536000)

                        self.stdout.write(self.style.SUCCESS(
                            'User Updated Successfully'))

                    else:
                        self.stderr.write(
                            'User Balance is more than Available Balance')

                else:
                    self.stderr.write('User Credential is not Valid')

            else:
                self.stdout.write(self.style.WARNING('User is Not Active'))

        except User.DoesNotExist:
            self.stderr.write('User does not exist')
