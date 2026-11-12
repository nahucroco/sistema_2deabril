import importlib
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APITestCase

from stories import tasks
from stories.models import StoryPost
from stories.services import ai_copy
from stories.views import InstagramAccountViewSet, StoryPostViewSet

from .helpers import MediaTemporalMixin, crear_cuenta, crear_post, png_subido


class ApiBase(MediaTemporalMixin, APITestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("duenio", password="clave-de-prueba")
        self.client.force_authenticate(self.usuario)
        self.cuenta = crear_cuenta()


class ConfigPermisosTests(SimpleTestCase):
    """El default de permisos sale de DEBUG al cargar settings.py."""

    def _settings_con(self, **variables):
        import config.settings as settings_module

        with mock.patch.dict(os.environ, variables):
            try:
                return importlib.reload(settings_module)
            finally:
                importlib.reload(settings_module)

    def _rest_framework_con(self, debug):
        return self._settings_con(DEBUG=debug, SECRET_KEY="clave-de-test").REST_FRAMEWORK

    def test_en_produccion_sin_secret_key_no_arranca(self):
        from django.core.exceptions import ImproperlyConfigured

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SECRET_KEY", None)
            with self.assertRaisesMessage(ImproperlyConfigured, "SECRET_KEY"):
                self._settings_con(DEBUG="False")

    def test_en_produccion_las_cookies_son_seguras(self):
        modulo = self._settings_con(DEBUG="False", SECRET_KEY="clave-de-test")
        self.assertTrue(modulo.SESSION_COOKIE_SECURE)
        self.assertTrue(modulo.CSRF_COOKIE_SECURE)
        self.assertEqual(modulo.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))

    def test_en_produccion_exige_login(self):
        self.assertEqual(
            self._rest_framework_con("False")["DEFAULT_PERMISSION_CLASSES"],
            ["rest_framework.permissions.IsAuthenticated"],
        )

    def test_en_desarrollo_permite_anonimo(self):
        self.assertEqual(
            self._rest_framework_con("True")["DEFAULT_PERMISSION_CLASSES"],
            ["rest_framework.permissions.AllowAny"],
        )


class PermisosProduccionTests(ApiBase):
    """Con IsAuthenticated (lo que queda en produccion) nada se ve sin login.

    DRF lee DEFAULT_PERMISSION_CLASSES al importar las vistas, asi que
    override_settings no alcanza: se fija el permiso en las vistas.
    """

    def setUp(self):
        super().setUp()
        for vista in (StoryPostViewSet, InstagramAccountViewSet):
            patcher = mock.patch.object(vista, "permission_classes", [IsAuthenticated])
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_anonimo_no_puede_listar_historias(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/historias/").status_code, status.HTTP_403_FORBIDDEN)

    def test_anonimo_no_puede_ver_cuentas(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/cuentas/").status_code, status.HTTP_403_FORBIDDEN)

    def test_logueado_si_puede(self):
        self.assertEqual(self.client.get("/api/historias/").status_code, status.HTTP_200_OK)


class CuentasApiTests(ApiBase):
    def test_lista_solo_cuentas_activas_y_nunca_el_token(self):
        crear_cuenta(nombre="Vieja", ig_user_id="999", activa=False)

        resp = self.client.get("/api/cuentas/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([c["nombre"] for c in resp.data], ["2 de Abril"])
        self.assertNotIn("access_token", resp.data[0])

    def test_no_se_pueden_crear_cuentas_por_api(self):
        resp = self.client.post("/api/cuentas/", {"nombre": "x", "ig_user_id": "1", "access_token": "t"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class HistoriasApiTests(ApiBase):
    def test_crear_historia_con_imagen(self):
        resp = self.client.post(
            "/api/historias/",
            {"cuenta": self.cuenta.id, "tipo": "oferta", "imagen": png_subido(), "titulo": "Rodado 29"},
            format="multipart",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["estado"], StoryPost.Estado.BORRADOR)
        self.assertIn("/media/historias/", resp.data["imagen_url_publica"])

    def test_no_se_puede_forzar_el_estado_ni_los_ids_de_meta(self):
        resp = self.client.post(
            "/api/historias/",
            {
                "cuenta": self.cuenta.id,
                "tipo": "oferta",
                "imagen": png_subido(),
                "estado": "publicada",
                "ig_media_id": "trucho",
            },
            format="multipart",
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        post = StoryPost.objects.get(pk=resp.data["id"])
        self.assertEqual(post.estado, StoryPost.Estado.BORRADOR)
        self.assertEqual(post.ig_media_id, "")

    def test_tipo_invalido_da_400(self):
        resp = self.client.post(
            "/api/historias/",
            {"cuenta": self.cuenta.id, "tipo": "cualquiera", "imagen": png_subido()},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tipo", resp.data)

    def test_sin_imagen_da_400(self):
        resp = self.client.post("/api/historias/", {"cuenta": self.cuenta.id, "tipo": "oferta"}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("imagen", resp.data)


class PublicarAhoraTests(ApiBase):
    def url(self, post):
        return f"/api/historias/{post.id}/publicar_ahora/"

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_encola_la_publicacion_y_marca_publicando(self, delay):
        post = crear_post(self.cuenta)

        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(self.url(post))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["estado"], StoryPost.Estado.PUBLICANDO)
        delay.assert_called_once_with(post.id)

    @mock.patch("stories.tasks.meta_graph.publicar_historia", return_value=("cont-1", "media-1"))
    def test_si_el_worker_termina_rapido_queda_publicada(self, _):
        """El worker puede terminar antes de que la vista responda: el estado final tiene que ser el del worker."""
        post = crear_post(self.cuenta)

        with mock.patch("stories.tasks.publicar_post.delay", side_effect=tasks.publicar_post):
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(self.url(post))

        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.PUBLICADA)

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_ya_publicada_da_409_y_no_encola(self, delay):
        for estado in (StoryPost.Estado.PUBLICADA, StoryPost.Estado.PUBLICANDO):
            with self.subTest(estado=estado):
                post = crear_post(self.cuenta, estado=estado)
                with self.captureOnCommitCallbacks(execute=True):
                    resp = self.client.post(self.url(post))
                self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        delay.assert_not_called()

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_una_con_error_se_puede_reintentar(self, delay):
        post = crear_post(self.cuenta, estado=StoryPost.Estado.ERROR, error_mensaje="Token vencido")

        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(self.url(post))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        delay.assert_called_once_with(post.id)

    def test_historia_inexistente_da_404(self):
        self.assertEqual(
            self.client.post("/api/historias/999999/publicar_ahora/").status_code, status.HTTP_404_NOT_FOUND
        )


class SugerirTextoApiTests(ApiBase):
    URL = "/api/historias/sugerir_texto/"

    @mock.patch("stories.views.ai_copy.sugerir_texto")
    def test_devuelve_lo_que_sugiere_claude(self, sugerir):
        sugerir.return_value = {"precio": "", "opciones": [{"titulo": "Hola", "detalle": ""}], "caption": ""}

        resp = self.client.post(self.URL, {"idea": "bici nueva", "tipo": "nueva"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["opciones"][0]["titulo"], "Hola")
        sugerir.assert_called_once_with(idea="bici nueva", tipo="nueva")

    @mock.patch("stories.views.ai_copy.sugerir_texto", side_effect=ai_copy.AICopyError("Falta la API key"))
    def test_error_de_ia_da_503_con_mensaje(self, _):
        resp = self.client.post(self.URL, {"idea": "bici", "tipo": "oferta"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(resp.data["detail"], "Falta la API key")

    @mock.patch("stories.views.ai_copy.sugerir_texto")
    def test_entrada_invalida_da_400_sin_llamar_a_claude(self, sugerir):
        resp = self.client.post(self.URL, {"idea": "", "tipo": "inventado"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("idea", resp.data)
        self.assertIn("tipo", resp.data)
        sugerir.assert_not_called()
