import os
import shutil
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from .models import FTPUser


@receiver(post_delete, sender=FTPUser)
def delete_ftp_directory(sender, instance, **kwargs):
    if instance.ftp_directory and os.path.exists(instance.ftp_directory):
        try:
            shutil.rmtree(instance.ftp_directory)
            print(f"Deleted FTP directory: {instance.ftp_directory}")
        except Exception as e:
            print(f"Error deleting FTP directory: {e}")
