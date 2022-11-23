from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import NotifierMessageChoices


User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('telegram_id')
        parser.add_argument('notifier_option')

    def handle(self, *args, **options):
        """Entry Point for Command"""
        self.telegram_id = options['telegram_id']
        self.notifier_option = options['notifier_option'].upper()

        try:
            user = User.objects.get(telegram_id=self.telegram_id)
            if self.notifier_option == 'DOLLAR':
                user.notifier_option = NotifierMessageChoices.DOLLAR
            elif self.notifier_option == 'PERCENT':
                user.notifier_option = NotifierMessageChoices.PERCENT
            # elif self.notifier_option == 'WITH_PERCENT':
                # user.notifier_option = NotifierMessageChoices.WITH_PERCENT
            else:
                self.stderr.write('Option does not exist')

            user.save()

            self.stdout.write(self.style.SUCCESS(
                'User Notifer Updated Successfully'))

        except User.DoesNotExist:
            self.stderr.write('User does not exist')
