from datetime import timedelta
from unittest import mock

from django.utils import timezone
from rest_framework.test import APITestCase

from stories import tasks
from stories.models import Repeticion, StoryPost

from .helpers import MediaTemporalMixin, crear_cuenta, crear_post, png_subido


class Base(MediaTemporalMixin, APITestCase):
    def setUp(self):
        self.cuenta = crear_cuenta()

    def crear_por_api(self, **extra):
        datos = {"cuenta": self.cuenta.id, "tipo": "oferta", "titulo": "Casco", "imagen": png_subido()}
        datos.update(extra)
        return self.client.post("/api/historias/", datos, format="multipart")


class PublicarFeedTests(Base):
    @mock.patch("stories.tasks.meta_graph.publicar_historia")
    @mock.patch("stories.tasks.meta_graph.publicar_feed", return_value=("cont-f", "media-f"))
    def test_el_feed_se_publica_con_su_texto(self, publicar_feed, publicar_historia):
        post = crear_post(self.cuenta, formato=StoryPost.Formato.FEED, caption="Llegaron cascos #bici")
        tasks.publicar_post(post.id)
        publicar_feed.assert_called_once_with(
            self.cuenta.ig_user_id, self.cuenta.access_token, post.imagen_url_publica, "Llegaron cascos #bici"
        )
        publicar_historia.assert_not_called()
        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.PUBLICADA)
        self.assertIsNone(post.vence_en)  # el feed no vence

    @mock.patch("stories.services.meta_graph._post", side_effect=[{"id": "cont"}, {"id": "media"}])
    def test_el_contenedor_del_feed_no_es_de_historia(self, _post):
        from stories.services import meta_graph

        meta_graph.publicar_feed("ig", "tok", "https://x/media/a.jpg", "Hola")
        datos = _post.call_args_list[0].args[1]
        self.assertEqual(datos["caption"], "Hola")
        self.assertNotIn("media_type", datos)


class ProgramarTests(Base):
    def test_con_fecha_queda_programada(self):
        cuando = timezone.now() + timedelta(hours=2)
        r = self.crear_por_api(formato="feed", caption="Hola", programada_para=cuando.isoformat())
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["estado"], "programada")

    def test_sin_fecha_queda_en_borrador(self):
        self.assertEqual(self.crear_por_api().json()["estado"], "borrador")

    def test_fecha_pasada_no_se_acepta(self):
        r = self.crear_por_api(programada_para=(timezone.now() - timedelta(hours=1)).isoformat())
        self.assertEqual(r.status_code, 400)

    def test_texto_del_feed_muy_largo(self):
        r = self.crear_por_api(formato="feed", caption="x" * 2201)
        self.assertEqual(r.status_code, 400)

    @mock.patch("stories.tasks.publicar_post.delay")
    def test_la_tarea_publica_la_programada_cuando_llega_la_hora(self, delay):
        post = crear_post(
            self.cuenta,
            formato=StoryPost.Formato.FEED,
            estado=StoryPost.Estado.PROGRAMADA,
            programada_para=timezone.now() - timedelta(minutes=1),
        )
        tasks.publish_due_posts()
        delay.assert_called_once_with(post.id)

    def test_cancelar_la_deja_en_borrador(self):
        post = crear_post(
            self.cuenta, estado=StoryPost.Estado.PROGRAMADA, programada_para=timezone.now() + timedelta(hours=1)
        )
        r = self.client.post(f"/api/historias/{post.id}/cancelar/")
        self.assertEqual(r.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.estado, StoryPost.Estado.BORRADOR)
        self.assertIsNone(post.programada_para)
        # Cancelar algo que ya no esta programado avisa en vez de pisarlo.
        self.assertEqual(self.client.post(f"/api/historias/{post.id}/cancelar/").status_code, 409)


class RegistroYRepeticionTests(Base):
    def test_el_feed_no_se_puede_repetir(self):
        post = crear_post(self.cuenta, formato=StoryPost.Formato.FEED)
        r = self.client.post(
            "/api/repeticiones/", {"historia": post.id, "cada_dias": 1, "hora": "10:00"}, format="json"
        )
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Repeticion.objects.exists())

    def test_registro_separa_programadas_y_no_mezcla_el_feed_con_las_historias_visibles(self):
        ahora = timezone.now()
        historia = crear_post(self.cuenta, estado=StoryPost.Estado.PUBLICADA, publicado_en=ahora)
        crear_post(self.cuenta, formato=StoryPost.Formato.FEED, estado=StoryPost.Estado.PUBLICADA, publicado_en=ahora)
        programada = crear_post(
            self.cuenta,
            formato=StoryPost.Formato.FEED,
            estado=StoryPost.Estado.PROGRAMADA,
            programada_para=ahora + timedelta(hours=3),
        )
        r = self.client.get("/api/historias/registro/").json()
        self.assertEqual([p["id"] for p in r["en_instagram"]], [historia.id])
        self.assertEqual([p["id"] for p in r["programadas"]], [programada.id])
        self.assertNotIn(programada.id, [p["id"] for p in r["recientes"]])
        self.assertEqual(len(r["recientes"]), 2)
