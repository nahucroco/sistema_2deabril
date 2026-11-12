"""
Corre una vez las tareas periodicas, sin necesitar Redis ni Celery beat.

En produccion (docker-compose.prod.yml) un contenedor lo ejecuta cada 5
minutos. Con CELERY_TASK_ALWAYS_EAGER=True las publicaciones que dispara
corren en este mismo proceso.
"""

from django.core.management.base import BaseCommand

from stories import tasks


class Command(BaseCommand):
    help = "Publica las historias programadas vencidas, destraba las colgadas y renueva tokens por vencer."

    def handle(self, *args, **options):
        tasks.marcar_publicaciones_colgadas()
        tasks.publish_due_posts()
        tasks.refresh_expiring_tokens()
