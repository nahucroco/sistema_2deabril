import importlib.util
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

_spec = importlib.util.spec_from_file_location("serve_media", Path(settings.BASE_DIR) / "scripts" / "serve_media.py")
serve_media = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(serve_media)


class ServeMediaTests(SimpleTestCase):
    """El servidor del tunel tiene que servir solo imagenes de media/, nada mas."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raiz = Path(self.tmp.name)
        self.media = raiz / "media"
        (self.media / "historias").mkdir(parents=True)
        (self.media / "historias" / "foto.png").write_bytes(b"png")
        (self.media / "historias" / "notas.txt").write_text("x")
        (raiz / "db.sqlite3").write_text("secreto")
        self._original = serve_media.MEDIA_ROOT
        serve_media.MEDIA_ROOT = self.media.resolve()
        self.addCleanup(setattr, serve_media, "MEDIA_ROOT", self._original)

    def test_sirve_una_imagen_de_media(self):
        self.assertEqual(serve_media.resolver("/media/historias/foto.png"), (self.media / "historias" / "foto.png").resolve())

    def test_ignora_query_string(self):
        self.assertIsNotNone(serve_media.resolver("/media/historias/foto.png?x=1"))

    def test_no_sirve_fuera_de_media(self):
        for path in (
            "/db.sqlite3",
            "/media/../db.sqlite3",
            "/media/%2e%2e/db.sqlite3",
            "/media/historias/../../db.sqlite3",
        ):
            with self.subTest(path=path):
                self.assertIsNone(serve_media.resolver(path))

    def test_no_sirve_archivos_que_no_son_imagenes_ni_carpetas(self):
        self.assertIsNone(serve_media.resolver("/media/historias/notas.txt"))
        self.assertIsNone(serve_media.resolver("/media/historias/"))
        self.assertIsNone(serve_media.resolver("/media/historias/no-existe.png"))
