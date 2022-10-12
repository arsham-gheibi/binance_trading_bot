from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.cache import cache
from django.conf import settings
from app.celery import celery_app
from core.models import Queue
from core.endpoints import ACCOUNT_BALANCE, SYMBOLS
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
        parser.add_argument('user_name')
        parser.add_argument('api_key')
        parser.add_argument('api_secret')
        parser.add_argument('balance')
        parser.add_argument('usage_percentage')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.user_name = options['user_name']
        self.api_key = options['api_key']
        self.api_secret = options['api_secret']
        self.balance = float(options['balance'])
        self.usage_percentage = (float(options['usage_percentage']))

        queues = Queue.objects.filter(is_available=True)
        main_queue = queues.filter(is_main=True)
        stream_queue = queues.filter(is_stream=True)
        notifier_queue = queues.filter(is_notifier=True)

        if main_queue.count() > 0 and \
            stream_queue.count() > 0 and \
                notifier_queue.count() > 0:

            main_queue = main_queue.first()
            stream_queue = stream_queue.first()
            notifier_queue = notifier_queue.first()

            try:
                user = User.objects.create_user(
                    self.api_key,
                    self.api_secret,
                    self.telegram_id,
                    self.user_name,
                    self.usage_percentage
                )

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
                        user.main_queue = main_queue
                        user.stream_queue = stream_queue
                        user.notifier_queue = notifier_queue
                        user.save()

                        main_queue.is_available = False
                        stream_queue.is_available = False
                        notifier_queue.is_available = False

                        main_queue.save()
                        stream_queue.save()
                        notifier_queue.save()

                        res = requests.get(SYMBOLS)
                        symbols = json.loads(res.content.decode('utf-8'))
                        celery_app.send_task(
                            'core.tasks.user_set_leverage',
                            [user.id, symbols],
                            queue=user.main_queue.name)
                        stream_task = celery_app.send_task(
                            'core.tasks.user_data_stream',
                            [user.id],
                            time_limit=31536000,
                            soft_time_limit=31536000,
                            queue=user.stream_queue.name)
                        notifier_task = celery_app.send_task(
                            'core.tasks.notifier',
                            [user.id],
                            time_limit=31536000,
                            soft_time_limit=31536000,
                            queue=user.notifier_queue.name)

                        cache.set(
                            user.id,
                            [stream_task.task_id, notifier_task.task_id],
                            31536000)

                        self.stdout.write(self.style.SUCCESS(
                            'User Created Successfully'))

                    else:
                        user.delete()
                        self.stdout.write(self.style.ERROR(
                            'User Balance is more than Available Balance'))

                else:
                    user.delete()
                    self.stdout.write(self.style.ERROR(
                        'User Credential is not Valid'))

            except IntegrityError:
                self.stdout.write(self.style.WARNING(
                    'Credential Already Exists'))

        else:
            self.stdout.write(self.style.WARNING(
                'There is no Available Worker at the Moment'))
