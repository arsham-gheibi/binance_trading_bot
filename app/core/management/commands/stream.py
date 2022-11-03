from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from app.celery import celery_app
from core.endpoints import SYMBOLS
import requests
import json


User = get_user_model()
BINANCE_ENDPOINT = settings.BINANCE_ENDPOINT


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Setting Tasks ..'))
        users = User.objects.filter(is_active=True)
        res = requests.get(SYMBOLS)
        symbols = json.loads(res.content.decode('utf-8'))

        # Terminating reserved tasks
        task_types = (
            'core.tasks.user_data_stream',
        )

        reserved_tasks = celery_app.control.inspect().reserved()

        # for worker in reserved_tasks:
        #     workers_tasks = reserved_tasks[worker]
        #     for task in workers_tasks:
        #         task_id = task['id']
        #         task_type = task['type']
        #         if task_type in task_types:
        #             celery_app.control.terminate(task_id)

        for user in users:
            celery_app.send_task(
                'core.tasks.user_set_leverage',
                [user.id, symbols],
                queue=user.main_queue.name
            )

            stream_task = celery_app.send_task(
                'core.tasks.user_data_stream',
                [user.id],
                time_limit=31536000,
                soft_time_limit=31536000,
                queue=user.stream_queue.name
            )

            cache.set(user.id, stream_task.task_id, 31536000)

        self.stdout.write(self.style.NOTICE('Tasks Setted'))
