from django.db import migrations


def create_queue(apps, schema_editor):
    Queue = apps.get_model('core', 'Queue')
    for queue_number in range(1, 6):
        Queue.objects.get_or_create(
            name=f'main_queue{queue_number}',
            is_main=True
        )

        Queue.objects.get_or_create(
            name=f'stream_queue{queue_number}',
            is_stream=True
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_queue_is_notifier_remove_user_notifier_queue'),
    ]

    operations = [
        migrations.RunPython(create_queue),
    ]
