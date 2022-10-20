from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from app.celery import celery_app


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']

        user = User.objects.get(telegram_id=self.telegram_id)
        if user.is_active:
            user.main_queue.is_available = True
            user.stream_queue.is_available = True
            user.notifier_queue.is_available = True
            user.is_active = False

            user.main_queue.save()
            user.stream_queue.save()
            user.notifier_queue.save()

            user.main_queue = None
            user.notifier_queue = None
            user.stream_queue = None
            user.save()

            tasks = cache.get(user.id)

            for task_id in tasks:
                celery_app.control.terminate(task_id)

            self.stdout.write(self.style.WARNING('User Disabled'))

        else:
            self.stderr.write('User is Already Disabled')
