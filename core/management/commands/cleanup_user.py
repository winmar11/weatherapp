from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.models import AlertHistory, AlertPreference, SavedLocation, UserSetting, WeatherSearch


class Command(BaseCommand):
    help = "Disable or delete a user and related data."

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to clean up")
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the user and related records (default: disable alerts only)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        delete = options["delete"]

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if not user:
            raise CommandError(f"User '{username}' not found")

        if delete:
            AlertHistory.objects.filter(alert__user=user).delete()
            AlertPreference.objects.filter(user=user).delete()
            WeatherSearch.objects.filter(user=user).delete()
            SavedLocation.objects.filter(user=user).delete()
            UserSetting.objects.filter(user=user).delete()
            user.delete()
            self.stdout.write(f"Deleted user '{username}' and related records.")
            return

        AlertPreference.objects.filter(user=user).update(is_active=False)
        self.stdout.write(f"Disabled alerts for user '{username}'.")
