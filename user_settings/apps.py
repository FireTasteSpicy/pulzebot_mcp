from django.apps import AppConfig


class UserSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_settings'
    verbose_name = 'User Settings'
    
    def ready(self):
        # Import signal handlers when app is ready
        try:
            import user_settings.signals
        except ImportError:
            pass
