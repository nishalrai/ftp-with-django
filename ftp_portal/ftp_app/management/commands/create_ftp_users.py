import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from ftp_app.models import FTPUser

class Command(BaseCommand):
    help = 'Creates FTPUser records for existing users without them'

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)
        created_count = 0
        skipped_count = 0

        for user in users:
            if not FTPUser.objects.filter(user=user).exists():
                ftp_dir = os.path.join(settings.MEDIA_ROOT, f'ftp_users/{user.username}')
                os.makedirs(ftp_dir, exist_ok=True)
                FTPUser.objects.create(
                    user=user,
                    ftp_directory=ftp_dir
                )
                self.stdout.write(self.style.SUCCESS(f'Created FTPUser for {user.username}'))
                created_count += 1
            else:
                self.stdout.write(f'FTPUser already exists for {user.username}')
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'Completed: {created_count} FTPUsers created, {skipped_count} skipped'))
        