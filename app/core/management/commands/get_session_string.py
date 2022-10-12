from django.core.management.base import BaseCommand
from django.conf import settings
from pyrogram import Client
import uvloop
import asyncio


TELEGRAM_API_ID = settings.TELEGRAM_API_ID
TELEGRAM_API_HASH = settings.TELEGRAM_API_HASH
TELEGRAM_PHONE_NUMBER = settings.TELEGRAM_PHONE_NUMBER


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Entry Point for Command"""
        async def main():
            uvloop.install()
            async with Client(
                "BINANCE",
                TELEGRAM_API_ID,
                TELEGRAM_API_HASH,
                phone_number=TELEGRAM_PHONE_NUMBER,
                in_memory=True
            ) as app:
                self.stdout.write(await app.export_session_string())

        asyncio.run(main())
