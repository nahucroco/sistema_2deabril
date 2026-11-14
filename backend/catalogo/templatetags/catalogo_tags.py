from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def absoluta(context, ruta):
    """URL absoluta (con https://dominio) para las vistas previas de WhatsApp y redes."""
    return context["request"].build_absolute_uri(ruta)
