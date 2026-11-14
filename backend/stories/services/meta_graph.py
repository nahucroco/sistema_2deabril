"""
Wrapper fino sobre la Graph API de Meta para publicar historias en Instagram.

Referencia: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing

Flujo (dos pasos):
  1. crear_contenedor(...)  -> POST /{ig_user_id}/media         -> container_id
  2. publicar(...)          -> POST /{ig_user_id}/media_publish -> media_id

Para video (Reels) hay que sondear el status_code del contenedor hasta
que sea FINISHED antes de publicar; para imagen de historia no hace falta,
pero igual se deja esperar_contenedor_listo por si se usa con video.
"""

from __future__ import annotations

import time

import requests
from django.conf import settings


class GraphAPIError(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


def _base_url() -> str:
    return f"https://graph.facebook.com/{settings.GRAPH_API_VERSION}"


def _post(path: str, data: dict) -> dict:
    resp = requests.post(f"{_base_url()}/{path}", data=data, timeout=30)
    payload = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        error = payload.get("error", {})
        raise GraphAPIError(
            error.get("message", f"Error HTTP {resp.status_code} de la Graph API"),
            response=payload,
        )
    return payload


def _get(path: str, params: dict) -> dict:
    resp = requests.get(f"{_base_url()}/{path}", params=params, timeout=30)
    payload = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        error = payload.get("error", {})
        raise GraphAPIError(
            error.get("message", f"Error HTTP {resp.status_code} de la Graph API"),
            response=payload,
        )
    return payload


def crear_contenedor_historia(ig_user_id: str, access_token: str, image_url: str) -> str:
    """Crea un contenedor de historia (imagen) y devuelve su id (creation_id)."""
    data = _post(
        f"{ig_user_id}/media",
        {
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": access_token,
        },
    )
    return data["id"]


def crear_contenedor_feed(ig_user_id: str, access_token: str, image_url: str, caption: str = "") -> str:
    """Crea un contenedor de post de feed (imagen) y devuelve su id."""
    data = _post(
        f"{ig_user_id}/media",
        {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
    )
    return data["id"]


def estado_contenedor(container_id: str, access_token: str) -> str:
    """FINISHED, IN_PROGRESS, ERROR o EXPIRED. Solo relevante para video."""
    data = _get(container_id, {"fields": "status_code", "access_token": access_token})
    return data.get("status_code", "FINISHED")


def esperar_contenedor_listo(container_id: str, access_token: str, intentos: int = 10, espera_seg: int = 5) -> None:
    for _ in range(intentos):
        estado = estado_contenedor(container_id, access_token)
        if estado == "FINISHED":
            return
        if estado in ("ERROR", "EXPIRED"):
            raise GraphAPIError(f"El contenedor {container_id} termino en estado {estado}")
        time.sleep(espera_seg)
    raise GraphAPIError(f"El contenedor {container_id} no termino de procesarse a tiempo")


def publicar(ig_user_id: str, access_token: str, container_id: str) -> str:
    """Publica un contenedor ya creado y devuelve el media_id resultante."""
    data = _post(
        f"{ig_user_id}/media_publish",
        {
            "creation_id": container_id,
            "access_token": access_token,
        },
    )
    return data["id"]


def publicar_historia(ig_user_id: str, access_token: str, image_url: str) -> tuple[str, str]:
    """Atajo: crea el contenedor de historia y lo publica. Devuelve (container_id, media_id)."""
    container_id = crear_contenedor_historia(ig_user_id, access_token, image_url)
    media_id = publicar(ig_user_id, access_token, container_id)
    return container_id, media_id


def publicar_feed(ig_user_id: str, access_token: str, image_url: str, caption: str = "") -> tuple[str, str]:
    """Atajo: crea el contenedor del post de feed (JPEG) y lo publica. Devuelve (container_id, media_id)."""
    container_id = crear_contenedor_feed(ig_user_id, access_token, image_url, caption)
    media_id = publicar(ig_user_id, access_token, container_id)
    return container_id, media_id


def cuentas_instagram_asignadas(access_token: str) -> list[dict]:
    """
    Cuentas de Instagram a las que tiene acceso un token de Unified login
    (token de usuario del sistema). Devuelve [{"id": ..., "username": ...}, ...].
    """
    data = _get("me/assigned_instagram_accounts", {"fields": "id,username", "access_token": access_token})
    return data.get("data", [])


def datos_cuenta(ig_user_id: str, access_token: str) -> dict:
    """Lee id y @usuario de una cuenta: sirve para comprobar que el token funciona con ella."""
    return _get(ig_user_id, {"fields": "id,username", "access_token": access_token})


def renovar_token_larga_duracion(access_token: str) -> dict:
    """
    Renueva un token de larga duracion que todavia no vencio (se puede
    renovar desde que tiene mas de 24hs de antiguedad, hasta antes de
    los 60 dias). Devuelve {"access_token": ..., "expires_in": segundos}.
    """
    return _get(
        "refresh_access_token",
        {
            "grant_type": "ig_refresh_token",
            "access_token": access_token,
        },
    )
