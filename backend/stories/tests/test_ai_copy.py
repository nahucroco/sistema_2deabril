import json
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase, override_settings

from stories.services import ai_copy


def mensaje_de_claude(texto):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=texto)])


RESPUESTA_OK = {
    "precio": "$450.000",
    "opciones": [
        {"titulo": "Rodado 29 a nuevo", "detalle": "Lista para salir"},
        {"titulo": "", "detalle": "sin titulo, se descarta"},
        {"titulo": "Oferta de la semana", "detalle": "Hasta agotar stock"},
        {"titulo": "Pasala a buscar", "detalle": "En el local"},
        {"titulo": "Cuarta opcion", "detalle": "sobra"},
    ],
    "caption": "Llego la bici que buscabas. #bici #oferta",
}


@override_settings(ANTHROPIC_API_KEY="sk-ant-test")
class SugerirTextoTests(SimpleTestCase):
    def setUp(self):
        patcher = mock.patch("anthropic.Anthropic")
        self.Anthropic = patcher.start()
        self.addCleanup(patcher.stop)
        self.crear = self.Anthropic.return_value.messages.create

    @override_settings(ANTHROPIC_API_KEY="")
    def test_sin_api_key_falla_con_mensaje_claro(self):
        with self.assertRaisesMessage(ai_copy.AICopyError, "ANTHROPIC_API_KEY"):
            ai_copy.sugerir_texto("bici rodado 29", "oferta")
        self.Anthropic.assert_not_called()

    def test_devuelve_hasta_tres_opciones_con_titulo(self):
        self.crear.return_value = mensaje_de_claude(json.dumps(RESPUESTA_OK))

        resultado = ai_copy.sugerir_texto("bici rodado 29 a 450 lucas", "oferta")

        self.assertEqual(resultado["precio"], "$450.000")
        self.assertEqual(
            [o["titulo"] for o in resultado["opciones"]],
            ["Rodado 29 a nuevo", "Oferta de la semana", "Pasala a buscar"],
        )
        self.assertIn("#bici", resultado["caption"])

    def test_tolera_texto_alrededor_del_json(self):
        self.crear.return_value = mensaje_de_claude("Aca va:\n```json\n" + json.dumps(RESPUESTA_OK) + "\n```")

        self.assertEqual(len(ai_copy.sugerir_texto("idea", "nueva")["opciones"]), 3)

    def test_el_prompt_incluye_la_idea_y_el_tipo_legible(self):
        self.crear.return_value = mensaje_de_claude(json.dumps(RESPUESTA_OK))

        ai_copy.sugerir_texto("service completo a 20 mil", "taller")

        self.Anthropic.assert_called_once_with(api_key="sk-ant-test")
        prompt = self.crear.call_args.kwargs["messages"][0]["content"]
        self.assertIn("service completo a 20 mil", prompt)
        self.assertIn("Servicio de taller", prompt)

    def test_respuesta_sin_json_levanta_error(self):
        self.crear.return_value = mensaje_de_claude("No puedo ayudarte con eso.")

        with self.assertRaisesMessage(ai_copy.AICopyError, "JSON valido"):
            ai_copy.sugerir_texto("idea", "oferta")

    def test_json_sin_opciones_utilizables_levanta_error(self):
        self.crear.return_value = mensaje_de_claude(json.dumps({"opciones": [{"titulo": ""}], "caption": "x"}))

        with self.assertRaisesMessage(ai_copy.AICopyError, "opciones"):
            ai_copy.sugerir_texto("idea", "oferta")

    def test_campos_faltantes_quedan_vacios(self):
        self.crear.return_value = mensaje_de_claude(json.dumps({"opciones": [{"titulo": "Solo titulo"}]}))

        resultado = ai_copy.sugerir_texto("idea", "aviso")

        self.assertEqual(resultado["precio"], "")
        self.assertEqual(resultado["caption"], "")
