from django.core.validators import MaxValueValidator, MinValueValidator
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
    """Una publicacion armada en el Taller: historia (9:16) o post del feed (4:5)."""

    class Formato(models.TextChoices):
        HISTORIA = "historia", "Historia"
        FEED = "feed", "Publicación del feed"

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
    formato = models.CharField(max_length=10, choices=Formato.choices, default=Formato.HISTORIA)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    imagen = models.ImageField(upload_to="historias/%Y/%m/")

    titulo = models.CharField(max_length=80, blank=True)
    detalle = models.CharField(max_length=140, blank=True)
    precio = models.CharField(max_length=40, blank=True)
    caption = models.TextField(blank=True, help_text="Texto para el feed, si corresponde")

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    programada_para = models.DateTimeField(null=True, blank=True)

    repeticion = models.ForeignKey(
        "Repeticion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publicaciones",
        help_text="Si la publico sola una repeticion automatica.",
    )

    ig_container_id = models.CharField(max_length=64, blank=True)
    ig_media_id = models.CharField(max_length=64, blank=True)
    error_mensaje = models.TextField(blank=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    publicado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
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

    @property
    def vence_en(self):
        """Cuando deja de verse en Instagram (las historias duran 24 horas; el feed queda)."""
        if self.formato != self.Formato.HISTORIA or self.estado != self.Estado.PUBLICADA or not self.publicado_en:
            return None
        return self.publicado_en + timezone.timedelta(hours=24)


def _en_hora_local(fecha, hora):
    """datetime con zona horaria del local para esa fecha y hora."""
    return timezone.make_aware(timezone.datetime.combine(fecha, hora))


class Repeticion(models.Model):
    """
    Una historia guardada que se vuelve a publicar sola cada tantos dias, a
    una hora fija. Cada vez se crea un StoryPost nuevo con la misma imagen,
    asi queda el registro de cada publicacion (y de los errores).
    """

    historia = models.ForeignKey(StoryPost, on_delete=models.CASCADE, related_name="repeticiones")
    nombre = models.CharField(max_length=80, blank=True)
    cada_dias = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="1 = todos los dias, 7 = una vez por semana.",
    )
    hora = models.TimeField(help_text="Hora del local en que se publica.")
    hasta = models.DateField(null=True, blank=True, help_text="Ultimo dia en que se publica. Vacio = sin fin.")
    activa = models.BooleanField(default=True)
    proxima = models.DateTimeField(help_text="Cuando se publica la proxima vez.")
    ultima = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Repeticion automatica"
        verbose_name_plural = "Repeticiones automaticas"
        ordering = ["proxima"]

    def __str__(self):
        return self.nombre or f"Repeticion de la historia {self.historia_id}"

    def primera_desde(self, ahora=None):
        """Primer horario a partir de ahora: hoy a la hora elegida si todavia no paso, si no mañana."""
        ahora = ahora or timezone.now()
        candidata = _en_hora_local(timezone.localdate(ahora), self.hora)
        if candidata <= ahora:
            candidata = _en_hora_local(timezone.localdate(ahora) + timezone.timedelta(days=1), self.hora)
        return candidata

    def siguiente_despues(self, ahora=None):
        """
        Proximo horario despues de una publicacion: suma cada_dias a la anterior
        hasta pasar ahora (si el servidor estuvo apagado, no publica de mas para ponerse al dia).
        """
        ahora = ahora or timezone.now()
        fecha = timezone.localdate(self.proxima)
        siguiente = self.proxima
        while siguiente <= ahora:
            fecha += timezone.timedelta(days=self.cada_dias)
            siguiente = _en_hora_local(fecha, self.hora)
        return siguiente

    def termino(self, momento):
        return bool(self.hasta and timezone.localdate(momento) > self.hasta)
