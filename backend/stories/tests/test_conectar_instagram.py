from io import StringIO
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase

from stories.models import InstagramAccount
from stories.services.meta_graph import GraphAPIError

from .helpers import crear_cuenta

MODULO = "stories.management.commands.conectar_instagram"


@mock.patch(f"{MODULO}.getpass", return_value="  token-nuevo  ")
@mock.patch(f"{MODULO}.meta_graph.datos_cuenta", return_value={"id": "178", "username": "bicicleteria_2_de_abril"})
class ConectarInstagramTests(TestCase):
    def correr(self, *args):
        salida = StringIO()
        call_command("conectar_instagram", *args, stdout=salida)
        return salida.getvalue()

    @mock.patch(f"{MODULO}.meta_graph.cuentas_instagram_asignadas", return_value=[{"id": "178", "username": "x"}])
    def test_averigua_la_cuenta_y_la_guarda_sin_vencimiento(self, _asignadas, datos, _getpass):
        salida = self.correr()

        cuenta = InstagramAccount.objects.get()
        self.assertEqual(cuenta.ig_user_id, "178")
        self.assertEqual(cuenta.access_token, "token-nuevo")
        self.assertIsNone(cuenta.token_expires_at)
        self.assertIn("@bicicleteria_2_de_abril", salida)
        self.assertNotIn("token-nuevo", salida)
        datos.assert_called_once_with("178", "token-nuevo")

    @mock.patch(f"{MODULO}.meta_graph.cuentas_instagram_asignadas")
    def test_actualiza_el_token_si_la_cuenta_ya_existe(self, asignadas, _datos, _getpass):
        crear_cuenta(ig_user_id="178", access_token="viejo", activa=False)

        self.correr("--ig-user-id", "178")

        asignadas.assert_not_called()
        cuenta = InstagramAccount.objects.get()
        self.assertEqual(cuenta.access_token, "token-nuevo")
        self.assertTrue(cuenta.activa)

    @mock.patch(f"{MODULO}.meta_graph.cuentas_instagram_asignadas", return_value=[{"id": "1"}, {"id": "2"}])
    def test_con_varias_cuentas_pide_elegir(self, _asignadas, _datos, _getpass):
        with self.assertRaisesMessage(CommandError, "--ig-user-id"):
            self.correr()
        self.assertFalse(InstagramAccount.objects.exists())

    @mock.patch(f"{MODULO}.meta_graph.cuentas_instagram_asignadas", return_value=[])
    def test_sin_cuentas_asignadas_falla(self, _asignadas, _datos, _getpass):
        with self.assertRaisesMessage(CommandError, "ninguna cuenta"):
            self.correr()

    @mock.patch(f"{MODULO}.meta_graph.cuentas_instagram_asignadas", return_value=[{"id": "178"}])
    def test_token_que_no_funciona_no_se_guarda(self, _asignadas, datos, _getpass):
        datos.side_effect = GraphAPIError("Invalid OAuth access token")

        with self.assertRaisesMessage(CommandError, "Invalid OAuth access token"):
            self.correr()
        self.assertFalse(InstagramAccount.objects.exists())

    def test_token_vacio_falla(self, _datos, getpass):
        getpass.return_value = "   "
        with self.assertRaisesMessage(CommandError, "token"):
            self.correr()
