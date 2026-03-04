from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Configuration for the tasks application."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.tasks'
    verbose_name = 'Tasks'
