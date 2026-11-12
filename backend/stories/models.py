from django.db import models
from django.utils import timezone


class InstagramAccount(models.Model):
    """
    Una cuenta profesional de Instagram conectada (la del local).

    El access_token de larga duracion vence a los 60 dias y hay que
    renovarlo antes (ver stories.tasks.refresh_expiring_tokens). Por ahora
    se guarda en texto plano en la base: para produccion conviene cifrarlo
    (por ejemplo con django-cryptography o un campo custom) antes de tener
    usuarios reales con acceso a la base.
    """

    nombre = models.CharField(max_length=80, help_text="Como identificarla en el admin, ej. '2 de Abril'")
    ig_user_id = models.CharField(
        max_length=64, unique=True, help_text="Instagram Business Account ID (no el @usuario)"
    )
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuenta de Instagram"
        verbose_name_plural = "Cuentas de Instagram"

    def __str__(self):
        return self.nombre

    @property
    def token_por_vencer(self):
        if not self.token_expires_at:
            return False
        return self.token_expires_at - timezone.now() < timezone.timedelta(days=7)


class StoryPost(models.Model):
    """Una historia (o mas adelante, post de feed) generada en el taller."""

    class Tipo(models.TextChoices):
        OFERTA = "oferta", "Oferta"
        NUEVA = "nueva", "Recien llegada"
        USADA = "usada", "Usada en venta"
        TALLER = "taller", "Servicio de taller"
        AVISO = "aviso", "Aviso"

    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PROGRAMADA = "programada", "Programada"
        PUBLICANDO = "publicando", "Publicando"
        PUBLICADA = "publicada", "Publicada"
        ERROR = "error", "Error al publicar"

    cuenta = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name="posts")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    imagen = models.ImageField(upload_to="historias/%Y/%m/")

    titulo = models.CharField(max_length=80, blank=True)
    detalle = models.CharField(max_length=140, blank=True)
    precio = models.CharField(max_length=40, blank=True)
    caption = models.TextField(blank=True, help_text="Texto para el feed, si corresponde")

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    programada_para = models.DateTimeField(null=True, blank=True)

    ig_container_id = models.CharField(max_length=64, blank=True)
    ig_media_id = models.CharField(max_length=64, blank=True)
    error_mensaje = models.TextField(blank=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    publicado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Historia"
        verbose_name_plural = "Historias"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.titulo or 'sin titulo'} ({self.estado})"

    @property
    def imagen_url_publica(self):
        """
        URL publica absoluta de la imagen, la que necesita leer Meta.

        PUBLIC_MEDIA_BASE_URL apunta a la carpeta de media en si (por ejemplo
        https://dominio.com/media), asi en local se puede exponer solo esa
        carpeta por un tunel sin dejar la API abierta a internet.
        """
        from django.conf import settings

        if not self.imagen:
            return None
        return f"{settings.PUBLIC_MEDIA_BASE_URL.rstrip('/')}/{self.imagen.name}"
