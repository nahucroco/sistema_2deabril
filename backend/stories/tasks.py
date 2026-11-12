import logging

from celery import shared_task
from django.utils import timezone

from .models import InstagramAccount, StoryPost
from .services import meta_graph

logger = logging.getLogger(__name__)


@shared_task
def publicar_post(post_id: int) -> None:
    """Publica una historia puntual ya sea al tocar 'Publicar ahora' o cuando Celery beat la encuentra vencida."""
    try:
        post = StoryPost.objects.select_related("cuenta").get(pk=post_id)
    except StoryPost.DoesNotExist:
        logger.warning("publicar_post: StoryPost %s no existe", post_id)
        return

    if post.estado == StoryPost.Estado.PUBLICADA:
        # Una tarea duplicada en la cola no tiene que publicarla dos veces en Instagram.
        logger.info("publicar_post: StoryPost %s ya estaba publicada, se ignora", post_id)
        return

    post.estado = StoryPost.Estado.PUBLICANDO
    post.error_mensaje = ""
    post.save(update_fields=["estado", "error_mensaje"])

    cuenta = post.cuenta
    image_url = post.imagen_url_publica

    try:
        container_id, media_id = meta_graph.publicar_historia(
            cuenta.ig_user_id, cuenta.access_token, image_url
        )
    except meta_graph.GraphAPIError as exc:
        post.estado = StoryPost.Estado.ERROR
        post.error_mensaje = str(exc)
        post.save(update_fields=["estado", "error_mensaje"])
        logger.error("Error publicando StoryPost %s: %s", post_id, exc)
        return

    post.ig_container_id = container_id
    post.ig_media_id = media_id
    post.estado = StoryPost.Estado.PUBLICADA
    post.publicado_en = timezone.now()
    post.save(update_fields=["ig_container_id", "ig_media_id", "estado", "publicado_en"])


@shared_task
def publish_due_posts() -> None:
    """Tarea periodica (cada 5 min): dispara las historias programadas que ya vencieron."""
    ahora = timezone.now()
    vencidas = StoryPost.objects.filter(
        estado=StoryPost.Estado.PROGRAMADA, programada_para__lte=ahora
    )
    for post_id in vencidas.values_list("id", flat=True):
        # Se pasa a PUBLICANDO antes de encolar, y solo si sigue PROGRAMADA:
        # asi la proxima corrida de beat (o una corrida en paralelo) no la
        # vuelve a encolar mientras el worker todavia no la tomo.
        tomada = StoryPost.objects.filter(pk=post_id, estado=StoryPost.Estado.PROGRAMADA).update(
            estado=StoryPost.Estado.PUBLICANDO
        )
        if tomada:
            publicar_post.delay(post_id)


@shared_task
def refresh_expiring_tokens() -> None:
    """Tarea periodica (diaria): renueva los tokens que vencen en menos de 7 dias."""
    for cuenta in InstagramAccount.objects.filter(activa=True):
        if not cuenta.token_por_vencer:
            continue
        try:
            data = meta_graph.renovar_token_larga_duracion(cuenta.access_token)
        except meta_graph.GraphAPIError as exc:
            logger.error("No se pudo renovar el token de %s: %s", cuenta.nombre, exc)
            continue
        cuenta.access_token = data["access_token"]
        cuenta.token_expires_at = timezone.now() + timezone.timedelta(seconds=data.get("expires_in", 0))
        cuenta.save(update_fields=["access_token", "token_expires_at"])
        logger.info("Token renovado para %s", cuenta.nombre)
