from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from app.celery import celery_app
from core.models import Signal
from core.utils import create_new_signal, is_signal_cancelled, find_symbol
from pyrogram import Client
import uvloop
import json


User = get_user_model()

TELEGRAM_API_ID = settings.TELEGRAM_API_ID
TELEGRAM_API_HASH = settings.TELEGRAM_API_HASH
TELEGRAM_PHONE_NUMBER = settings.TELEGRAM_PHONE_NUMBER
TELEGRAM_SESSION_STRING = settings.TELEGRAM_SESSION_STRING
TELEGRAM_CHANNEL_TITLE = settings.TELEGRAM_CHANNEL_TITLE


class Command(BaseCommand):
    def handle(self, *args, **options):
        uvloop.install()
        app = Client(
            "BINANCE",
            TELEGRAM_API_ID,
            TELEGRAM_API_HASH,
            phone_number=TELEGRAM_PHONE_NUMBER,
            session_string=TELEGRAM_SESSION_STRING)

        self.stdout.write(self.style.SUCCESS('Listening for Signals'))

        @app.on_message()
        def log(client, message):
            message = json.loads(str(message))
            try:
                message_type = message['chat']['type']
                message_sender = ''

                if message_type == 'ChatType.CHANNEL':
                    message_sender = message['chat']['title']

                elif message_type == 'ChatType.BOT':
                    message_sender = message['chat']['first_name']

                if message_sender == TELEGRAM_CHANNEL_TITLE:
                    text = message['text']

                    try:
                        reply_text = message['reply_to_message']['text']
                        symbol = find_symbol(reply_text)
                        signal = Signal.objects.filter(symbol=symbol).first()

                        if signal is not None:
                            if is_signal_cancelled(text):
                                users = User.objects.filter(is_active=True)
                                for user in users:
                                    celery_app.send_task(
                                        'core.tasks.cancel_order',
                                        [user.id, signal.symbol],
                                        queue=user.main_queue.name)

                                self.stdout.write(self.style.WARNING(
                                    f'#{signal.symbol} Signal is Cancelled'))

                            else:
                                # Sending a Signal as reply message
                                create_new_signal(text)
                        else:
                            # Sending a Signal as reply message
                            create_new_signal(text)

                    except KeyError:
                        # Sending a Signal a normal telegram message
                        create_new_signal(text)

            except KeyError:
                pass

        app.run()
