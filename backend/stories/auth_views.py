"""
Login por sesion para el Taller.

El front pregunta primero por /api/sesion/ (que ademas deja la cookie de
CSRF), y si hace falta muestra la pantalla de login, que postea a
/api/sesion/iniciar/. Los usuarios se crean con createsuperuser o desde
el admin: no hay registro abierto.
"""

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle


def _estado(request):
    return {
        "usuario": request.user.get_username() if request.user.is_authenticated else None,
        # En DEBUG la API no pide login (ver settings.REST_FRAMEWORK), asi que el front tampoco.
        "requiere_login": not settings.DEBUG,
    }


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def sesion(request):
    return Response(_estado(request))


class LoginThrottle(AnonRateThrottle):
    """Limita los intentos de login por IP (tasa en settings: DEFAULT_THROTTLE_RATES["login"])."""

    scope = "login"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def iniciar_sesion(request):
    usuario = authenticate(
        request,
        username=str(request.data.get("usuario", "")).strip(),
        password=str(request.data.get("clave", "")),
    )
    if usuario is None or not usuario.is_active:
        return Response({"detail": "Usuario o contraseña incorrectos."}, status=status.HTTP_400_BAD_REQUEST)
    login(request, usuario)
    return Response(_estado(request))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cerrar_sesion(request):
    logout(request)
    return Response(_estado(request))
