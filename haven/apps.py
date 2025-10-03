from django.apps import AppConfig


class HavenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'haven'
    
    def ready(self):
        import haven.signals