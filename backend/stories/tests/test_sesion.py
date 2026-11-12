from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class SesionTests(APITestCase):
    def setUp(self):
        cache.clear()  # el throttle de login guarda los intentos en cache
        self.client = APIClient(enforce_csrf_checks=True)
        get_user_model().objects.create_user("duenio", password="clave-de-prueba")

    def csrf(self):
        return self.client.cookies["csrftoken"].value

    def test_sesion_anonima_deja_cookie_csrf(self):
        resp = self.client.get("/api/sesion/")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["usuario"])
        self.assertIn("csrftoken", self.client.cookies)

    @override_settings(DEBUG=False)
    def test_en_produccion_pide_login(self):
        self.assertTrue(self.client.get("/api/sesion/").data["requiere_login"])

    @override_settings(DEBUG=True)
    def test_en_desarrollo_no_pide_login(self):
        self.assertFalse(self.client.get("/api/sesion/").data["requiere_login"])

    def test_login_correcto_y_despues_salir(self):
        self.client.get("/api/sesion/")

        resp = self.client.post(
            "/api/sesion/iniciar/", {"usuario": " duenio ", "clave": "clave-de-prueba"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["usuario"], "duenio")
        self.assertEqual(self.client.get("/api/sesion/").data["usuario"], "duenio")

        resp = self.client.post("/api/sesion/cerrar/", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.client.get("/api/sesion/").data["usuario"])

    def test_cerrar_sesion_sin_token_csrf_falla(self):
        self.client.get("/api/sesion/")
        self.client.post("/api/sesion/iniciar/", {"usuario": "duenio", "clave": "clave-de-prueba"}, format="json")

        self.assertEqual(self.client.post("/api/sesion/cerrar/").status_code, status.HTTP_403_FORBIDDEN)

    def test_clave_incorrecta_da_400_con_mensaje(self):
        resp = self.client.post("/api/sesion/iniciar/", {"usuario": "duenio", "clave": "otra"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("incorrectos", resp.data["detail"])

    def test_usuario_inactivo_no_entra(self):
        get_user_model().objects.filter(username="duenio").update(is_active=False)

        resp = self.client.post(
            "/api/sesion/iniciar/", {"usuario": "duenio", "clave": "clave-de-prueba"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_frena_los_intentos_repetidos(self):
        for _ in range(10):
            self.client.post("/api/sesion/iniciar/", {"usuario": "duenio", "clave": "mal"}, format="json")

        resp = self.client.post(
            "/api/sesion/iniciar/", {"usuario": "duenio", "clave": "clave-de-prueba"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
