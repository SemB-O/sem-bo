from django.apps import AppConfig


class CboConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cbo'

    def ready(self):
        from django.contrib.auth.management import commands as auth_commands
        from django.core.management import call_command
        import cbo.signals 