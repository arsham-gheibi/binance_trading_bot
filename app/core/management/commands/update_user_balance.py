from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()
BINANCE_ENDPOINT = settings.BINANCE_ENDPOINT


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')
        parser.add_argument('balance')
        parser.add_argument('usage_percentage')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.balance = float(options['balance'])
        self.usage_percentage = (float(options['usage_percentage']))

        user = User.objects.get(telegram_id=self.telegram_id)
        if user.is_active:
            try:
                account_balance = session.get_wallet_balance(
                    coin="USDT")['result']['USDT']['available_balance']

                if self.balance < account_balance * 2:
                    user.balance = self.balance
                    user.usage_percentage = self.usage_percentage
                    user.save()

                    self.stdout.write(
                        self.style.SUCCESS('User Balance Updated'))

                else:
                    self.stdout.write(self.style.ERROR(
                        'User Balance is more than Available Balance'))

            except InvalidRequestError:
                self.stdout.write(self.style.ERROR(
                    'User Credential is not Valid'))

        else:
            self.stdout.write(self.style.ERROR('User is not Active'))
