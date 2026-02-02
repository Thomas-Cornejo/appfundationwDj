from django.apps import AppConfig


class EngagementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "engagements"

    def ready(self):
        import engagements.signals
