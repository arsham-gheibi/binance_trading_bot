from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from app.celery import celery_app


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')
        parser.add_argument('bot_token')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.bot_token = options['bot_token']

        try:
            user = User.objects.get(telegram_id=self.telegram_id)
            user.bot_token = self.bot_token
            user.save()

            task_id = cache.get(user.id)
            celery_app.control.terminate(task_id)

            stream_task = celery_app.send_task(
                'core.tasks.user_data_stream',
                [user.id],
                time_limit=31536000,
                queue=user.stream_queue.name
            )

            cache.set(user.id, stream_task.task_id, 31536000)

            self.stdout.write(self.style.SUCCESS(
                'User Updated Successfully'))

        except User.DoesNotExist:
            self.stderr.write('User does not exist')
