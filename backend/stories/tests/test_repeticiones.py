from datetime import date, datetime, time, timedelta
from unittest import mock

from django.utils import timezone
from rest_framework.test import APITestCase

from stories import tasks
from stories.models import Repeticion, StoryPost

from .helpers import MediaTemporalMixin, crear_cuenta, crear_post


def local(*args):
    return timezone.make_aware(datetime(*args))


def en(momento):
    """Congela el reloj en ese momento (hora del local)."""
    return mock.patch("django.utils.timezone.now", return_value=momento)


class Base(MediaTemporalMixin, APITestCase):
    def setUp(self):
        self.cuenta = crear_cuenta()
        self.base = crear_post(self.cuenta, titulo="Abierto los sábados")

    def crear_rep(self, **kwargs):
        datos = {"historia": self.base, "cada_dias": 1, "hora": time(10, 0), "proxima": local(2026, 11, 14, 10, 0)}
        datos.update(kwargs)
        return Repeticion.objects.create(**datos)


class CalculoDeHorariosTests(Base):
    def test_primera_vez_hoy_si_la_hora_no_paso(self):
        rep = self.crear_rep()
        self.assertEqual(rep.primera_desde(local(2026, 11, 14, 9, 0)), local(2026, 11, 14, 10, 0))

    def test_primera_vez_mañana_si_la_hora_ya_paso(self):
        rep = self.crear_rep()
        self.assertEqual(rep.primera_desde(local(2026, 11, 14, 10, 0)), local(2026, 11, 15, 10, 0))

    def test_siguiente_suma_los_dias_elegidos(self):
        rep = self.crear_rep(cada_dias=7)
        self.assertEqual(rep.siguiente_despues(local(2026, 11, 14, 10, 1)), local(2026, 11, 21, 10, 0))

    def test_si_el_servidor_estuvo_apagado_no_publica_de_mas(self):
        rep = self.crear_rep(cada_dias=2)
        # Pasaron 5 dias: salta directo al proximo horario futuro.
        self.assertEqual(rep.siguiente_despues(local(2026, 11, 19, 12, 0)), local(2026, 11, 20, 10, 0))


@mock.patch("stories.tasks.publicar_post.delay")
class PublicarRepeticionesTests(Base):
    def test_publica_una_copia_y_mueve_la_proxima(self, delay):
        rep = self.crear_rep()
        with en(local(2026, 11, 14, 10, 3)):
            self.assertEqual(tasks.publicar_repeticiones(), 1)
        copia = StoryPost.objects.get(repeticion=rep)
        self.assertEqual(copia.imagen.name, self.base.imagen.name)
        self.assertEqual(copia.titulo, "Abierto los sábados")
        self.assertEqual(copia.estado, StoryPost.Estado.PUBLICANDO)
        delay.assert_called_once_with(copia.id)
        rep.refresh_from_db()
        self.assertEqual(rep.proxima, local(2026, 11, 15, 10, 0))
        self.assertEqual(rep.ultima, local(2026, 11, 14, 10, 3))

    def test_antes_de_hora_no_hace_nada(self, delay):
        self.crear_rep()
        with en(local(2026, 11, 14, 9, 59)):
            self.assertEqual(tasks.publicar_repeticiones(), 0)
        delay.assert_not_called()

    def test_dos_corridas_seguidas_publican_una_sola_vez(self, delay):
        self.crear_rep()
        with en(local(2026, 11, 14, 10, 3)):
            tasks.publicar_repeticiones()
            tasks.publicar_repeticiones()
        self.assertEqual(delay.call_count, 1)

    def test_pausada_no_se_publica(self, delay):
        self.crear_rep(activa=False)
        with en(local(2026, 11, 14, 10, 3)):
            tasks.publicar_repeticiones()
        delay.assert_not_called()

    def test_el_ultimo_dia_publica_y_despues_se_apaga(self, delay):
        rep = self.crear_rep(hasta=date(2026, 11, 14))
        with en(local(2026, 11, 14, 10, 3)):
            tasks.publicar_repeticiones()
        delay.assert_called_once()
        rep.refresh_from_db()
        self.assertFalse(rep.activa)

    def test_vencida_sin_publicar_se_apaga(self, delay):
        rep = self.crear_rep(hasta=date(2026, 11, 13))
        with en(local(2026, 11, 14, 10, 3)):
            tasks.publicar_repeticiones()
        delay.assert_not_called()
        rep.refresh_from_db()
        self.assertFalse(rep.activa)

    def test_lo_corre_el_comando_de_tareas_periodicas(self, delay):
        from django.core.management import call_command

        self.crear_rep(proxima=timezone.now() - timedelta(minutes=1))
        with mock.patch("stories.tasks.refresh_expiring_tokens"):
            call_command("tareas_periodicas")
        delay.assert_called_once()


class RepeticionesApiTests(Base):
    def test_crear_calcula_la_primera_vez_y_usa_el_titulo(self):
        with en(local(2026, 11, 14, 11, 0)):
            r = self.client.post(
                "/api/repeticiones/", {"historia": self.base.id, "cada_dias": 7, "hora": "10:00"}, format="json"
            )
        self.assertEqual(r.status_code, 201, r.content)
        rep = Repeticion.objects.get()
        self.assertEqual(rep.nombre, "Abierto los sábados")
        self.assertEqual(rep.proxima, local(2026, 11, 15, 10, 0))  # hoy ya paso: mañana

    def test_cambiar_la_hora_recalcula_y_pausar_no(self):
        rep = self.crear_rep(proxima=local(2026, 11, 15, 10, 0))
        with en(local(2026, 11, 14, 11, 0)):
            self.client.patch(f"/api/repeticiones/{rep.id}/", {"activa": False}, format="json")
            rep.refresh_from_db()
            self.assertEqual(rep.proxima, local(2026, 11, 15, 10, 0))
            self.client.patch(f"/api/repeticiones/{rep.id}/", {"hora": "18:30", "activa": True}, format="json")
        rep.refresh_from_db()
        self.assertTrue(rep.activa)
        self.assertEqual(rep.proxima, local(2026, 11, 14, 18, 30))

    def test_reanudar_no_publica_lo_atrasado(self):
        rep = self.crear_rep(activa=False, proxima=local(2026, 11, 1, 10, 0))
        with en(local(2026, 11, 14, 11, 0)):
            self.client.patch(f"/api/repeticiones/{rep.id}/", {"activa": True}, format="json")
        rep.refresh_from_db()
        self.assertEqual(rep.proxima, local(2026, 11, 15, 10, 0))

    def test_valida_datos(self):
        r = self.client.post(
            "/api/repeticiones/", {"historia": self.base.id, "cada_dias": 0, "hora": "10:00"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        r = self.client.post(
            "/api/repeticiones/",
            {"historia": self.base.id, "cada_dias": 1, "hora": "10:00", "hasta": "2000-01-01"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_borrar_no_borra_lo_publicado(self):
        rep = self.crear_rep()
        publicada = crear_post(self.cuenta, repeticion=rep, estado=StoryPost.Estado.PUBLICADA)
        self.assertEqual(self.client.delete(f"/api/repeticiones/{rep.id}/").status_code, 204)
        publicada.refresh_from_db()
        self.assertIsNone(publicada.repeticion)

    def test_registro_separa_lo_visible_de_lo_reciente(self):
        ahora = timezone.now()
        visible = crear_post(self.cuenta, titulo="Visible", estado=StoryPost.Estado.PUBLICADA, publicado_en=ahora)
        vieja = crear_post(
            self.cuenta, titulo="Vieja", estado=StoryPost.Estado.PUBLICADA, publicado_en=ahora - timedelta(hours=30)
        )
        crear_post(self.cuenta, titulo="Con error", estado=StoryPost.Estado.ERROR)
        r = self.client.get("/api/historias/registro/").json()
        self.assertEqual([p["id"] for p in r["en_instagram"]], [visible.id])
        self.assertIsNotNone(r["en_instagram"][0]["vence_en"])
        titulos = {p["titulo"] for p in r["recientes"]}
        self.assertEqual(titulos, {"Visible", "Vieja", "Con error"})  # sin el borrador base
        self.assertNotIn(vieja.id, [p["id"] for p in r["en_instagram"]])
