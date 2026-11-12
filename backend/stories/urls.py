from django.urls import path
from rest_framework.routers import DefaultRouter

from .auth_views import cerrar_sesion, iniciar_sesion, sesion
from .views import InstagramAccountViewSet, StoryPostViewSet

router = DefaultRouter()
router.register("cuentas", InstagramAccountViewSet, basename="cuenta")
router.register("historias", StoryPostViewSet, basename="historia")

urlpatterns = [
    path("sesion/", sesion, name="sesion"),
    path("sesion/iniciar/", iniciar_sesion, name="sesion-iniciar"),
    path("sesion/cerrar/", cerrar_sesion, name="sesion-cerrar"),
] + router.urls
