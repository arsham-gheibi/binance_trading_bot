from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from app.celery import celery_app


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
                try:
                    account_balance = session.get_wallet_balance(
                        coin="USDT")['result']['USDT']['available_balance']

                    if self.balance < account_balance * 2:
                        user.api_key = self.api_key
                        user.api_secret = self.api_secret
                        user.balance = self.balance
                        user.usage_percentage = self.usage_percentage
                        user.save()

                        tasks = cache.get(user.id)

                        for task_id in tasks:
                            celery_app.control.terminate(task_id)

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
                            'User Updated Successfully'))

                    else:
                        self.stdout.write(self.style.ERROR(
                            'User Balance is more than Available Balance'))

                except InvalidRequestError:
                    self.stdout.write(self.style.ERROR(
                        'User Credential is not Valid'))
            else:
                self.stdout.write(self.style.WARNING('User is Not Active'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User does not exist'))
