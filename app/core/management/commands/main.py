from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from core.utils import analyze_reply_message
import asyncio
import uvloop
import threading
import websockets
import json


User = get_user_model()

TELEGRAM_LISTENER_WEBSOCKET = settings.TELEGRAM_LISTENER_WEBSOCKET
TELEGRAM_LISTENER_TOKEN = settings.TELEGRAM_LISTENER_TOKEN


class Command(BaseCommand):
    def handle(self, *args, **options):
        async def keep_alive(websocket):
            pong_waiter = await websocket.ping()
            await pong_waiter

        async def main():
            self.stdout.write(self.style.SUCCESS('Listening for Signals'))
            while True:
                async with websockets.connect(
                    TELEGRAM_LISTENER_WEBSOCKET
                ) as websocket:
                    asyncio.create_task(keep_alive(websocket))
                    await websocket.send(TELEGRAM_LISTENER_TOKEN)
                    res = await websocket.recv()
                    message = json.loads(res)['message']
                    threading.Thread(
                        target=analyze_reply_message, args=([message])).start()
        uvloop.install()
        asyncio.run(main())
