from django.core.management.base import BaseCommand
from core.models import Precision


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('symbol')
        parser.add_argument('block')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.symbol = options['symbol']
        self.block = options['block'].lower() == 'block'

        try:
            precision = Precision.objects.get(symbol=self.symbol)
            if self.block:
                precision.is_blacklisted = True
                self.stdout.write(self.style.WARNING(
                    'Coin added to Blacklist'))

            else:
                precision.is_blacklisted = False
                self.stdout.write(self.style.NOTICE(
                    'Coin removed from Blacklist'))

            precision.save()

        except Precision.DoesNotExist:
            self.stderr.write('Precision Does Not Exist')
