from unittest import mock

from django.test import SimpleTestCase, override_settings

from stories.services import meta_graph


def respuesta(status_code=200, json_data=None):
    resp = mock.Mock()
    resp.status_code = status_code
    resp.content = b"{}" if json_data is not None else b""
    resp.json.return_value = json_data or {}
    return resp


@override_settings(GRAPH_API_VERSION="v21.0")
class MetaGraphTests(SimpleTestCase):
    @mock.patch("stories.services.meta_graph.requests.post")
    def test_publicar_historia_crea_contenedor_y_lo_publica(self, post):
        post.side_effect = [respuesta(json_data={"id": "cont-1"}), respuesta(json_data={"id": "media-1"})]

        resultado = meta_graph.publicar_historia("ig-1", "tok", "https://x/foto.png")

        self.assertEqual(resultado, ("cont-1", "media-1"))
        primera, segunda = post.call_args_list
        self.assertEqual(primera.args[0], "https://graph.facebook.com/v21.0/ig-1/media")
        self.assertEqual(
            primera.kwargs["data"],
            {"image_url": "https://x/foto.png", "media_type": "STORIES", "access_token": "tok"},
        )
        self.assertEqual(segunda.args[0], "https://graph.facebook.com/v21.0/ig-1/media_publish")
        self.assertEqual(segunda.kwargs["data"], {"creation_id": "cont-1", "access_token": "tok"})

    @mock.patch("stories.services.meta_graph.requests.post")
    def test_error_de_la_api_levanta_graph_api_error_con_el_mensaje_de_meta(self, post):
        cuerpo = {"error": {"message": "Invalid OAuth access token", "code": 190}}
        post.return_value = respuesta(400, cuerpo)

        with self.assertRaises(meta_graph.GraphAPIError) as ctx:
            meta_graph.crear_contenedor_historia("ig-1", "tok", "https://x/foto.png")

        self.assertEqual(str(ctx.exception), "Invalid OAuth access token")
        self.assertEqual(ctx.exception.response, cuerpo)

    @mock.patch("stories.services.meta_graph.requests.post")
    def test_error_sin_cuerpo_usa_un_mensaje_generico(self, post):
        post.return_value = respuesta(502, None)

        with self.assertRaisesMessage(meta_graph.GraphAPIError, "Error HTTP 502"):
            meta_graph.publicar("ig-1", "tok", "cont-1")

    @mock.patch("stories.services.meta_graph.requests.post")
    def test_crear_contenedor_feed_manda_el_caption(self, post):
        post.return_value = respuesta(json_data={"id": "cont-2"})

        self.assertEqual(meta_graph.crear_contenedor_feed("ig-1", "tok", "https://x/f.png", "Hola"), "cont-2")
        self.assertEqual(post.call_args.kwargs["data"]["caption"], "Hola")
        self.assertNotIn("media_type", post.call_args.kwargs["data"])

    @mock.patch("stories.services.meta_graph.time.sleep")
    @mock.patch("stories.services.meta_graph.requests.get")
    def test_esperar_contenedor_sondea_hasta_finished(self, get, sleep):
        get.side_effect = [
            respuesta(json_data={"status_code": "IN_PROGRESS"}),
            respuesta(json_data={"status_code": "FINISHED"}),
        ]

        meta_graph.esperar_contenedor_listo("cont-1", "tok", espera_seg=1)

        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1)

    @mock.patch("stories.services.meta_graph.time.sleep")
    @mock.patch("stories.services.meta_graph.requests.get")
    def test_esperar_contenedor_falla_si_termina_en_error(self, get, sleep):
        get.return_value = respuesta(json_data={"status_code": "ERROR"})

        with self.assertRaisesMessage(meta_graph.GraphAPIError, "estado ERROR"):
            meta_graph.esperar_contenedor_listo("cont-1", "tok")
        sleep.assert_not_called()

    @mock.patch("stories.services.meta_graph.time.sleep")
    @mock.patch("stories.services.meta_graph.requests.get")
    def test_esperar_contenedor_se_rinde_despues_de_los_intentos(self, get, sleep):
        get.return_value = respuesta(json_data={"status_code": "IN_PROGRESS"})

        with self.assertRaisesMessage(meta_graph.GraphAPIError, "a tiempo"):
            meta_graph.esperar_contenedor_listo("cont-1", "tok", intentos=3)
        self.assertEqual(get.call_count, 3)

    @mock.patch("stories.services.meta_graph.requests.get")
    def test_renovar_token_pide_ig_refresh_token(self, get):
        get.return_value = respuesta(json_data={"access_token": "nuevo", "expires_in": 5184000})

        data = meta_graph.renovar_token_larga_duracion("viejo")

        self.assertEqual(data["access_token"], "nuevo")
        self.assertEqual(
            get.call_args.kwargs["params"], {"grant_type": "ig_refresh_token", "access_token": "viejo"}
        )
