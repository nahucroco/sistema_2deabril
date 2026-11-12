from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from stories import tasks
from stories.models import StoryPost
from stories.services.meta_graph import GraphAPIError

from .helpers import MediaTemporalMixin, crear_cuenta, crear_post


class PublicarPostTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta()

    @mock.patch("stories.tasks.meta_graph.publicar_historia", return_value=("cont-1", "media-1"))
    def test_publica_y_guarda_ids(self, publicar_historia):
        post = crear_post(self.cuenta)

        tasks.publicar_post(post.id)

        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.PUBLICADA)
        self.assertEqual(post.ig_container_id, "cont-1")
        self.assertEqual(post.ig_media_id, "media-1")
        self.assertIsNotNone(post.publicado_en)
        publicar_historia.assert_called_once_with(
            self.cuenta.ig_user_id, self.cuenta.access_token, post.imagen_url_publica
        )

    @mock.patch("stories.tasks.meta_graph.publicar_historia", side_effect=GraphAPIError("Token vencido"))
    def test_error_de_meta_deja_la_historia_en_error_con_el_mensaje(self, _):
        post = crear_post(self.cuenta)

        tasks.publicar_post(post.id)

        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.ERROR)
        self.assertEqual(post.error_mensaje, "Token vencido")
        self.assertEqual(post.ig_media_id, "")

    @mock.patch("stories.tasks.meta_graph.publicar_historia", return_value=("cont-2", "media-2"))
    def test_reintento_despues_de_un_error_limpia_el_mensaje(self, _):
        post = crear_post(self.cuenta, estado=StoryPost.Estado.ERROR, error_mensaje="Token vencido")

        tasks.publicar_post(post.id)

        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.PUBLICADA)
        self.assertEqual(post.error_mensaje, "")

    @mock.patch("stories.tasks.meta_graph.publicar_historia")
    def test_no_vuelve_a_publicar_una_historia_ya_publicada(self, publicar_historia):
        post = crear_post(self.cuenta, estado=StoryPost.Estado.PUBLICADA, ig_media_id="media-viejo")

        tasks.publicar_post(post.id)

        publicar_historia.assert_not_called()
        post.refresh_from_db()
        self.assertEqual(post.ig_media_id, "media-viejo")

    @mock.patch("stories.tasks.meta_graph.publicar_historia")
    def test_post_inexistente_no_rompe(self, publicar_historia):
        tasks.publicar_post(999999)
        publicar_historia.assert_not_called()


class PublishDuePostsTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta()
        self.ahora = timezone.now()

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_dispara_solo_las_programadas_vencidas(self, delay):
        vencida = crear_post(
            self.cuenta, estado=StoryPost.Estado.PROGRAMADA, programada_para=self.ahora - timedelta(minutes=1)
        )
        crear_post(self.cuenta, estado=StoryPost.Estado.PROGRAMADA, programada_para=self.ahora + timedelta(hours=1))
        crear_post(self.cuenta, estado=StoryPost.Estado.BORRADOR, programada_para=self.ahora - timedelta(hours=1))
        crear_post(self.cuenta, estado=StoryPost.Estado.PUBLICADA, programada_para=self.ahora - timedelta(hours=1))

        tasks.publish_due_posts()

        delay.assert_called_once_with(vencida.id)

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_no_encola_dos_veces_si_el_worker_todavia_no_la_tomo(self, delay):
        """Beat corre cada 5 min: si el worker esta atrasado, la misma historia no se tiene que encolar de nuevo."""
        crear_post(
            self.cuenta, estado=StoryPost.Estado.PROGRAMADA, programada_para=self.ahora - timedelta(minutes=1)
        )

        tasks.publish_due_posts()
        tasks.publish_due_posts()

        self.assertEqual(delay.call_count, 1)


class RefreshExpiringTokensTests(TestCase):
    @mock.patch(
        "stories.tasks.meta_graph.renovar_token_larga_duracion",
        return_value={"access_token": "nuevo", "expires_in": 60 * 24 * 3600},
    )
    def test_renueva_solo_los_tokens_por_vencer_de_cuentas_activas(self, renovar):
        ahora = timezone.now()
        por_vencer = crear_cuenta(ig_user_id="1", access_token="viejo", token_expires_at=ahora + timedelta(days=2))
        crear_cuenta(ig_user_id="2", access_token="lejano", token_expires_at=ahora + timedelta(days=40))
        crear_cuenta(ig_user_id="3", access_token="inactiva", token_expires_at=ahora + timedelta(days=2), activa=False)

        tasks.refresh_expiring_tokens()

        renovar.assert_called_once_with("viejo")
        por_vencer.refresh_from_db()
        self.assertEqual(por_vencer.access_token, "nuevo")
        self.assertGreater(por_vencer.token_expires_at, ahora + timedelta(days=59))

    @mock.patch(
        "stories.tasks.meta_graph.renovar_token_larga_duracion",
        side_effect=[GraphAPIError("Token invalido"), {"access_token": "nuevo-b", "expires_in": 3600}],
    )
    def test_si_una_cuenta_falla_sigue_con_las_demas(self, _):
        vence = timezone.now() + timedelta(days=1)
        a = crear_cuenta(ig_user_id="a", access_token="tok-a", token_expires_at=vence)
        b = crear_cuenta(ig_user_id="b", access_token="tok-b", token_expires_at=vence)

        tasks.refresh_expiring_tokens()

        a.refresh_from_db()
        b.refresh_from_db()
        self.assertEqual(a.access_token, "tok-a")
        self.assertEqual(b.access_token, "nuevo-b")


class MarcarPublicacionesColgadasTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        self.cuenta = crear_cuenta()

    def _post_publicando_hace(self, minutos):
        post = crear_post(self.cuenta, estado=StoryPost.Estado.PUBLICANDO)
        StoryPost.objects.filter(pk=post.pk).update(actualizado=timezone.now() - timedelta(minutes=minutos))
        return post

    def test_pasa_a_error_las_que_llevan_mucho_en_publicando(self):
        colgada = self._post_publicando_hace(30)
        reciente = self._post_publicando_hace(2)

        self.assertEqual(tasks.marcar_publicaciones_colgadas(), 1)

        colgada.refresh_from_db()
        reciente.refresh_from_db()
        self.assertEqual(colgada.estado, StoryPost.Estado.ERROR)
        self.assertIn("interrumpió", colgada.error_mensaje)
        self.assertEqual(reciente.estado, StoryPost.Estado.PUBLICANDO)

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_una_programada_hace_rato_que_recien_se_toma_no_cuenta_como_colgada(self, _delay):
        """publish_due_posts la pasa a PUBLICANDO con un .update(): tiene que renovar 'actualizado'."""
        post = crear_post(
            self.cuenta, estado=StoryPost.Estado.PROGRAMADA, programada_para=timezone.now() - timedelta(hours=2)
        )
        StoryPost.objects.filter(pk=post.pk).update(actualizado=timezone.now() - timedelta(hours=3))

        tasks.publish_due_posts()
        tasks.marcar_publicaciones_colgadas()

        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.PUBLICANDO)


class TareasPeriodicasCommandTests(TestCase):
    @mock.patch("stories.tasks.refresh_expiring_tokens")
    @mock.patch("stories.tasks.publish_due_posts")
    @mock.patch("stories.tasks.marcar_publicaciones_colgadas")
    def test_corre_las_tres_tareas(self, colgadas, programadas, tokens):
        from django.core.management import call_command

        call_command("tareas_periodicas")

        colgadas.assert_called_once_with()
        programadas.assert_called_once_with()
        tokens.assert_called_once_with()
