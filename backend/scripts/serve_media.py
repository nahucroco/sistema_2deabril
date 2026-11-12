"""
Servidor minimo y de solo lectura para exponer las imagenes de backend/media
por un tunel (ngrok) mientras se prueba la publicacion en local.

Meta necesita descargar la imagen desde una URL publica. Este servidor sirve
UNICAMENTE archivos de imagen bajo /media/, sin listar carpetas, para no
exponer la API (que en DEBUG no pide login) ni la base ni el .env.

Uso (desde la carpeta backend):
    .venv/Scripts/python scripts/serve_media.py      # escucha en 127.0.0.1:8001
y en otra terminal:
    ngrok http 8001
"""

import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

MEDIA_ROOT = (Path(__file__).resolve().parent.parent / "media").resolve()
PREFIJO = "/media/"
EXTENSIONES = {".png", ".jpg", ".jpeg", ".webp"}


def resolver(path_url: str) -> Path | None:
    """Devuelve el archivo pedido si es una imagen dentro de MEDIA_ROOT, si no None."""
    path = unquote(urlsplit(path_url).path)
    if not path.startswith(PREFIJO):
        return None
    archivo = (MEDIA_ROOT / path[len(PREFIJO):]).resolve()
    if MEDIA_ROOT not in archivo.parents or archivo.suffix.lower() not in EXTENSIONES or not archivo.is_file():
        return None
    return archivo


class MediaHandler(BaseHTTPRequestHandler):
    def _responder(self, con_cuerpo: bool):
        archivo = resolver(self.path)
        if archivo is None:
            self.send_error(404)
            return
        datos = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(archivo.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        if con_cuerpo:
            self.wfile.write(datos)

    def do_GET(self):
        self._responder(con_cuerpo=True)

    def do_HEAD(self):
        self._responder(con_cuerpo=False)


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    print(f"Sirviendo solo imagenes de {MEDIA_ROOT} en http://127.0.0.1:{puerto}{PREFIJO}")
    ThreadingHTTPServer(("127.0.0.1", puerto), MediaHandler).serve_forever()
