from django.core.management.base import BaseCommand
from core.models import Queue


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Entry Point for Command"""
        for queue_number in range(1, 6):
            Queue.objects.get_or_create(
                name=f'main_queue{queue_number}',
                is_main=True
            )

            Queue.objects.get_or_create(
                name=f'stream_queue{queue_number}',
                is_stream=True
            )
