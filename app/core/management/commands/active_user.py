from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from app.celery import celery_app
from core.models import Queue


User = get_user_model()
BINANCE_ENDPOINT = settings.BINANCE_ENDPOINT


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')
        parser.add_argument('balance')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.balance = float(options['balance'])

        try:
            user = User.objects.get(telegram_id=self.telegram_id)
            if not user.is_active:
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
                        account_balance = session.get_wallet_balance(
                            coin="USDT")['result']['USDT']['available_balance']

                        if self.balance < account_balance * 2:
                            user.balance = self.balance
                            user.main_queue = main_queue
                            user.stream_queue = stream_queue
                            user.notifier_queue = notifier_queue
                            user.is_active = True
                            user.save()

                            main_queue.is_available = False
                            stream_queue.is_available = False
                            notifier_queue.is_available = False

                            main_queue.save()
                            stream_queue.save()
                            notifier_queue.save()

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
                                'User Activated Successfully'))

                        else:
                            self.stdout.write(self.style.ERROR(
                                'User Balance is more than Available Balance'))

                    except InvalidRequestError:
                        self.stdout.write(self.style.ERROR(
                            'User Credential is not Valid'))

                else:
                    self.stdout.write(self.style.WARNING(
                        'There is no Available Worker at the Moment'))
            else:
                self.stdout.write(self.style.WARNING(
                    'User is Already Active'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User does not exist'))
