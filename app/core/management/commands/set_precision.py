from django.core.management.base import BaseCommand
from core.models import Precision
from core.endpoints import EXCHANGE_INFO
import requests
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.stdout.write(self.style.NOTICE('Setting Precisions ..'))
        res = requests.get(EXCHANGE_INFO)
        symbols = json.loads(res.content.decode('utf-8'))['symbols']

        for symbol in symbols:
            filters = symbol['filters']
            name = symbol['symbol']
            tick_size = str(float(filters[0]['tickSize']))
            max_trading_qty = filters[1]['maxQty']
            min_trading_qty = filters[1]['minQty']
            qty_step = str(filters[1]['stepSize'])

            precision, _ = Precision.objects.get_or_create(symbol=name)
            precision.tick_size = len(tick_size.replace('.', '')) - 1
            precision.max_trading_qty = max_trading_qty
            precision.min_trading_qty = min_trading_qty
            precision.qty_step = len(qty_step.replace('.', '')) - 1
            precision.save()

        self.stdout.write(self.style.NOTICE('Precisions Set'))
