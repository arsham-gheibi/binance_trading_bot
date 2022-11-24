#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py migrate
python manage.py set_precision
celery -A app purge -f -Q stream_queue1,stream_queue2,stream_queue3,stream_queue4,stream_queue5
celery -A app beat -l info -s /vol/celerybeat-schedule &
celery -A app worker -l info -c 1 -n main_worker1 -Q main_queue1 &
celery -A app worker -l info -c 1 -n main_worker2 -Q main_queue2 &
celery -A app worker -l info -c 1 -n main_worker3 -Q main_queue3 &
celery -A app worker -l info -c 1 -n main_worker4 -Q main_queue4 &
celery -A app worker -l info -c 1 -n main_worker5 -Q main_queue5 &
celery -A app worker -l info -c 1 -n stream_worker1 -Q stream_queue1 &
celery -A app worker -l info -c 1 -n stream_worker2 -Q stream_queue2 &
celery -A app worker -l info -c 1 -n stream_worker3 -Q stream_queue3 &
celery -A app worker -l info -c 1 -n stream_worker4 -Q stream_queue4 &
celery -A app worker -l info -c 1 -n stream_worker5 -Q stream_queue5 &
python manage.py set_tasks
python manage.py main