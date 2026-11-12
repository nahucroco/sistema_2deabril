from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from stories.models import StoryPost

from .helpers import MediaTemporalMixin, crear_cuenta, crear_post


class InstagramAccountTests(TestCase):
    def test_token_sin_vencimiento_no_esta_por_vencer(self):
        cuenta = crear_cuenta(token_expires_at=None)
        self.assertFalse(cuenta.token_por_vencer)

    def test_token_que_vence_en_menos_de_7_dias_esta_por_vencer(self):
        cuenta = crear_cuenta(token_expires_at=timezone.now() + timedelta(days=6))
        self.assertTrue(cuenta.token_por_vencer)

    def test_token_que_vence_en_mas_de_7_dias_no_esta_por_vencer(self):
        cuenta = crear_cuenta(token_expires_at=timezone.now() + timedelta(days=30))
        self.assertFalse(cuenta.token_por_vencer)

    def test_token_ya_vencido_esta_por_vencer(self):
        cuenta = crear_cuenta(token_expires_at=timezone.now() - timedelta(days=1))
        self.assertTrue(cuenta.token_por_vencer)


class StoryPostTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta()

    def test_arranca_como_borrador(self):
        post = crear_post(self.cuenta)
        self.assertEqual(post.estado, StoryPost.Estado.BORRADOR)

    @override_settings(PUBLIC_MEDIA_BASE_URL="https://bici2deabril.example")
    def test_imagen_url_publica_es_absoluta(self):
        post = crear_post(self.cuenta)
        self.assertTrue(post.imagen_url_publica.startswith("https://bici2deabril.example/media/historias/"))
        self.assertTrue(post.imagen_url_publica.endswith(".png"))

    def test_imagen_url_publica_sin_imagen_es_none(self):
        post = crear_post(self.cuenta, imagen=None)
        self.assertIsNone(post.imagen_url_publica)

    def test_str_muestra_tipo_titulo_y_estado(self):
        post = crear_post(self.cuenta, titulo="")
        self.assertEqual(str(post), "Oferta — sin titulo (borrador)")
