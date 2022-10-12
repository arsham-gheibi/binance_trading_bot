from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.settings import BINANCE_ENDPOINT
from core.endpoints import ACCOUNT_BALANCE


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']

        try:
            user = User.objects.get(telegram_id=self.telegram_id)

            try:
                account_balance = session.get_wallet_balance(
                    coin="USDT")['result']['USDT']

                available = account_balance['available_balance']
                wallet = account_balance['wallet_balance']

                messages = [
                    f'Used Balance: {self.style.NOTICE(user.balance)}',
                    f'Wallet Balance: {self.style.NOTICE(wallet)}',
                    f'Available Balance: {self.style.NOTICE(available)}'
                ]

                for message in messages:
                    self.stdout.write(self.style.SUCCESS(message))

            except InvalidRequestError:
                self.stdout.write(self.style.ERROR(
                    'User Credential is not Valid'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'User Does Not Exist'))
