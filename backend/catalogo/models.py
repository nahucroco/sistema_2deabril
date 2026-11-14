import re
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image, ImageOps

# Las fotos del celular pesan varios MB: se guardan achicadas a este lado
# maximo, en JPEG. Ademas se les borran los metadatos (incluida la ubicacion GPS).
LADO_MAXIMO_FOTO = 1600


def achicar_foto(archivo):
    """Devuelve la foto como JPEG con el lado mayor <= LADO_MAXIMO_FOTO y sin metadatos."""
    archivo.seek(0)
    with Image.open(archivo) as original:
        img = ImageOps.exif_transpose(original)  # respeta la rotacion del celular
        img.thumbnail((LADO_MAXIMO_FOTO, LADO_MAXIMO_FOTO))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            fondo = Image.new("RGB", img.size, (255, 255, 255))
            fondo.paste(img, mask=img.getchannel("A"))
            img = fondo
        elif img.mode != "RGB":
            img = img.convert("RGB")
        salida = BytesIO()
        img.save(salida, "JPEG", quality=85, optimize=True)
    return ContentFile(salida.getvalue(), name=f"{Path(archivo.name).stem}.jpg")


def formatear_pesos(valor):
    """450000 -> '$ 450.000'."""
    return "$ " + f"{int(valor):,}".replace(",", ".")


class DatosNegocio(models.Model):
    """Datos de contacto que muestra la web. Hay un solo registro (pk=1)."""

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        help_text="Con código de país y de área, sin 0 ni 15. Ej.: 5493415551234",
    )
    direccion = models.CharField(
        "dirección", max_length=200, blank=True, help_text="Calle, número y localidad. Se usa también para el mapa."
    )
    horarios = models.TextField(
        blank=True, help_text="Una línea por renglón. Ej.: Lunes a viernes: 9 a 13 y 16 a 20 h"
    )
    instagram = models.CharField(max_length=60, blank=True, default="bicicleteria_2_de_abril", help_text="Sin @")

    class Meta:
        verbose_name = "Datos del negocio"
        verbose_name_plural = "Datos del negocio"

    def __str__(self):
        return "Datos del negocio"

    def save(self, *args, **kwargs):
        self.pk = 1
        self.whatsapp = re.sub(r"\D", "", self.whatsapp)
        self.instagram = self.instagram.strip().lstrip("@")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # es la configuracion del sitio: no se borra

    @classmethod
    def actual(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def link_whatsapp(self, texto=""):
        if not self.whatsapp:
            return ""
        url = f"https://wa.me/{self.whatsapp}"
        return f"{url}?text={quote(texto)}" if texto else url

    @property
    def whatsapp_general(self):
        return self.link_whatsapp("¡Hola! Vi la web de la bicicletería y quería hacer una consulta.")

    @property
    def whatsapp_taller(self):
        return self.link_whatsapp("¡Hola! Quería pedir un turno para el taller.")

    @property
    def lineas_horarios(self):
        return [linea.strip() for linea in self.horarios.splitlines() if linea.strip()]

    @property
    def link_mapa(self):
        if not self.direccion:
            return ""
        return f"https://www.google.com/maps/search/?api=1&query={quote(self.direccion)}"

    @property
    def mapa_embebido(self):
        if not self.direccion:
            return ""
        return f"https://www.google.com/maps?q={quote(self.direccion)}&output=embed"

    @property
    def link_instagram(self):
        return f"https://www.instagram.com/{self.instagram}/" if self.instagram else ""


class ProductoQuerySet(models.QuerySet):
    def publicos(self):
        """Los que se pueden abrir por link (los vendidos tambien, asi un link viejo no da error)."""
        return self.exclude(estado=Producto.Estado.OCULTO)

    def en_catalogo(self):
        """Los que se listan en el catalogo y en el inicio."""
        return self.filter(estado__in=[Producto.Estado.DISPONIBLE, Producto.Estado.RESERVADO])


class Producto(models.Model):
    class Categoria(models.TextChoices):
        NUEVA = "nueva", "Bicicletas nuevas"
        USADA = "usada", "Usadas"
        REPUESTO = "repuesto", "Repuestos"
        ACCESORIO = "accesorio", "Accesorios"

    class Estado(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        RESERVADO = "reservado", "Reservado"
        VENDIDO = "vendido", "Vendido"
        OCULTO = "oculto", "Oculto (no se muestra)"

    nombre = models.CharField(max_length=120)
    slug = models.SlugField(
        max_length=80, unique=True, blank=True, help_text="Parte final del link. Se completa sola con el nombre."
    )
    categoria = models.CharField("categoría", max_length=20, choices=Categoria.choices)
    detalle = models.CharField(max_length=140, blank=True, help_text="Una línea corta para la tarjeta del catálogo.")
    descripcion = models.TextField("descripción", blank=True)
    caracteristicas = models.TextField(
        "características",
        blank=True,
        help_text="Una por renglón, con dos puntos. Ej.: Rodado: 29",
    )
    rodado = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Solo para bicis: sirve para filtrar.")
    precio = models.PositiveIntegerField(null=True, blank=True, help_text="En pesos, sin puntos. Vacío = 'Consultar'.")
    precio_anterior = models.PositiveIntegerField(
        null=True, blank=True, help_text="Si está en oferta: el precio de antes, que aparece tachado."
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DISPONIBLE)
    destacado = models.BooleanField(default=False, help_text="Aparece en el inicio.")
    link_mercadolibre = models.URLField("link de Mercado Libre", blank=True)
    link_marketplace = models.URLField("link de Marketplace", blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = ProductoQuerySet.as_manager()

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:70] or "producto"
            slug, n = base, 2
            while Producto.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalogo:producto", args=[self.slug])

    @property
    def en_oferta(self):
        return bool(self.precio and self.precio_anterior and self.precio_anterior > self.precio)

    @property
    def etiqueta(self):
        """(texto, clase CSS) del cartelito de la tarjeta."""
        if self.en_oferta:
            return ("Oferta", "oferta")
        return {
            self.Categoria.NUEVA: ("Nueva", "nueva"),
            self.Categoria.USADA: ("Usada", "usada"),
            self.Categoria.REPUESTO: ("Repuesto", "neutra"),
            self.Categoria.ACCESORIO: ("Accesorio", "neutra"),
        }.get(self.categoria, ("", "neutra"))

    @property
    def precio_texto(self):
        return formatear_pesos(self.precio) if self.precio else "Consultar"

    @property
    def precio_anterior_texto(self):
        return formatear_pesos(self.precio_anterior) if self.en_oferta else ""

    @property
    def lista_caracteristicas(self):
        """[('Rodado', '29'), ...]; un renglon sin dos puntos queda con la clave vacia."""
        filas = []
        for linea in self.caracteristicas.splitlines():
            if not linea.strip():
                continue
            clave, sep, valor = linea.partition(":")
            filas.append((clave.strip(), valor.strip()) if sep else ("", linea.strip()))
        return filas

    @property
    def foto_principal(self):
        fotos = list(self.fotos.all())  # usa el prefetch si lo hay
        return fotos[0] if fotos else None


class FotoProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="productos/%Y/%m/")
    orden = models.PositiveSmallIntegerField(default=0, help_text="La de número más bajo es la principal.")

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "foto"
        verbose_name_plural = "fotos"

    def __str__(self):
        return f"Foto de {self.producto}"

    def save(self, *args, **kwargs):
        if self.imagen and not self.imagen._committed:
            self.imagen = achicar_foto(self.imagen)
        super().save(*args, **kwargs)


class ServicioTaller(models.Model):
    nombre = models.CharField(max_length=80)
    detalle = models.CharField(max_length=200, blank=True)
    precio = models.CharField(max_length=40, blank=True, help_text="Texto libre. Ej.: $ 25.000, desde $ 15.000")
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "servicio del taller"
        verbose_name_plural = "servicios del taller"

    def __str__(self):
        return self.nombre
