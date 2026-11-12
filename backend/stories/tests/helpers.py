"""Utilidades compartidas por los tests: fabricas de cuentas, historias e imagenes."""

import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from stories.models import InstagramAccount, StoryPost


def png_subido(nombre="foto.png"):
    """Un PNG real y chiquito, para que ImageField lo acepte."""
    buffer = io.BytesIO()
    Image.new("RGB", (9, 16), color=(20, 60, 140)).save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


def crear_cuenta(**kwargs):
    datos = {
        "nombre": "2 de Abril",
        "ig_user_id": "17841400000000000",
        "access_token": "token-de-prueba",
    }
    datos.update(kwargs)
    return InstagramAccount.objects.create(**datos)


def crear_post(cuenta, **kwargs):
    datos = {
        "cuenta": cuenta,
        "tipo": StoryPost.Tipo.OFERTA,
        "imagen": png_subido(),
        "titulo": "Rodado 29 en oferta",
    }
    datos.update(kwargs)
    return StoryPost.objects.create(**datos)


class MediaTemporalMixin:
    """Guarda las imagenes subidas en una carpeta temporal que se borra al terminar."""

    @classmethod
    def setUpClass(cls):
        cls._media_dir = tempfile.mkdtemp(prefix="test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
