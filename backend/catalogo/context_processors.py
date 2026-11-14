from django.utils.functional import SimpleLazyObject


def negocio(request):
    """Datos de contacto para el encabezado y el pie de la web. Solo consulta la base si se usan."""
    from .models import DatosNegocio

    return {"negocio": SimpleLazyObject(DatosNegocio.actual)}
