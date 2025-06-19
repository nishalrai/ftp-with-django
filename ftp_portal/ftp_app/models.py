from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import timedelta
from django.utils import timezone

class FTPUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    ftp_directory = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username

class ShareLink(models.Model):
    file_path = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    requires_auth = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"{self.file_path} ({self.uuid})"