from django.apps import AppConfig


class GamificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gamifications"

    def ready(self):
        import gamifications.signals
