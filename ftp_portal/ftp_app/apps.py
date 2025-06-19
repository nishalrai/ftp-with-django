from django.apps import AppConfig


class FtpAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ftp_app'

    def ready(self):
        import ftp_app.signals  # Import signals to register them
