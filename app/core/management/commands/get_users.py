from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


User = get_user_model()


user_info_message = """{user_name}
${balance} {usage_percentage}%
"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Entry Point for Command"""
        users = User.objects.all()
        active_users = users.filter(is_active=True)
        deactive_users = users.filter(is_active=False)

        for user in active_users:
            self.stdout.write(self.style.SUCCESS(
                user_info_message.format(
                    user_name=user.user_name,
                    balance=user.balance,
                    usage_percentage=user.usage_percentage
                )))

        for user in deactive_users:
            self.stdout.write(self.style.WARNING(
                user_info_message.format(
                    user_name=user.user_name,
                    balance=user.balance,
                    usage_percentage=user.usage_percentage
                )))
