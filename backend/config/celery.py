import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("sistema_2deabril")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Tareas periodicas: publicar lo que este programado y renovar el token antes de que venza.
app.conf.beat_schedule = {
    "publicar-historias-programadas": {
        "task": "stories.tasks.publish_due_posts",
        "schedule": crontab(minute="*/5"),
    },
    "destrabar-publicaciones-colgadas": {
        "task": "stories.tasks.marcar_publicaciones_colgadas",
        "schedule": crontab(minute="*/5"),
    },
    "renovar-token-instagram": {
        "task": "stories.tasks.refresh_expiring_tokens",
        "schedule": crontab(hour=4, minute=0),
    },
}
