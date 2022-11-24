from celery import Celery
from celery.schedules import crontab
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

celery_app = Celery('app')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()


celery_app.conf.beat_schedule = {
    'set_precision': {
        'task': 'core.tasks.set_precision',
        'schedule': crontab(minute=0, hour='*/4')
    },
    'set_leverage': {
        'task': 'core.tasks.set_leverage',
        'schedule': crontab(minute=0, hour='*/4')
    }
}
