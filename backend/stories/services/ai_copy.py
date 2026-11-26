"""
Sugerencias de texto con Claude (Anthropic API) para el paso 3 del taller.

Requiere ANTHROPIC_API_KEY en el entorno. Si no esta configurada, el
endpoint que usa esto devuelve un 503 claro en vez de romper.
"""

from __future__ import annotations

import json

from django.conf import settings

TIPO_LABELS = {
    "oferta": "Oferta",
    "nueva": "Recien llegada",
    "usada": "Usada en venta",
    "taller": "Servicio de taller",
    "aviso": "Aviso",
    "dos_fotos": "Novedades (dos fotos)",
    "cuatro_fotos": "Novedades (cuatro fotos)",
    "foto": "Foto sola, sin texto encima",
}


class AICopyError(Exception):
    pass


def sugerir_texto(idea: str, tipo: str) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        raise AICopyError("ANTHROPIC_API_KEY no esta configurada en el servidor.")

    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    tipo_label = TIPO_LABELS.get(tipo, tipo)

    prompt = (
        "Sos redactor de redes de una bicicleteria de barrio en Argentina (Bicicleteria 2 de Abril). "
        f'El dueno quiere publicar esto: "{idea[:600]}". '
        f"Tipo de publicacion: {tipo_label}. "
        "Responde solo con un JSON con esta forma: "
        '{"precio": "precio tal como se mostraria, por ejemplo $450.000, o cadena vacia si no se menciona", '
        '"opciones": [tres objetos {"titulo": "hasta 28 caracteres, sin emojis", "detalle": "hasta 60 caracteres"}], '
        '"caption": "2 o 3 oraciones en espanol rioplatense para el feed de Instagram, con 4 a 6 hashtags al final"}. '
        "No inventes datos que el dueno no dio (marca, modelo, precio, estado, cuotas)."
    )

    message = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")

    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError) as exc:
        raise AICopyError(f"Claude no devolvio un JSON valido: {text[:300]}") from exc

    opciones = [o for o in data.get("opciones", []) if o.get("titulo")][:3]
    if not opciones:
        raise AICopyError("La respuesta no trajo opciones de titulo utilizables.")

    return {
        "precio": data.get("precio", ""),
        "opciones": opciones,
        "caption": data.get("caption", ""),
    }
