from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import InstagramAccount, Repeticion, StoryPost
from .serializers import (
    InstagramAccountSerializer,
    RepeticionSerializer,
    StoryPostSerializer,
    SugerirTextoSerializer,
)
from .services import ai_copy
from .tasks import publicar_post


class InstagramAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura: la cuenta se carga desde el admin, no desde la app."""

    queryset = InstagramAccount.objects.filter(activa=True)
    serializer_class = InstagramAccountSerializer
    # Sin permission_classes propio: toma el default de settings.REST_FRAMEWORK
    # (AllowAny en DEBUG para poder probar el front sin loguearse, IsAuthenticated en produccion).


class StoryPostViewSet(viewsets.ModelViewSet):
    queryset = StoryPost.objects.all()
    serializer_class = StoryPostSerializer
    # Idem: default de settings.REST_FRAMEWORK segun DEBUG.

    @action(detail=True, methods=["post"])
    def publicar_ahora(self, request, pk=None):
        post = self.get_object()
        if post.estado in (StoryPost.Estado.PUBLICANDO, StoryPost.Estado.PUBLICADA):
            return Response(
                {"detail": "Esta historia ya se esta publicando o ya se publico."},
                status=status.HTTP_409_CONFLICT,
            )
        # Primero se marca PUBLICANDO y recien despues de guardar se encola:
        # si se encolaba antes, un worker rapido podia dejarla PUBLICADA y
        # esta vista la pisaba de vuelta a PUBLICANDO para siempre.
        post.estado = StoryPost.Estado.PUBLICANDO
        post.save(update_fields=["estado", "actualizado"])
        transaction.on_commit(lambda: publicar_post.delay(post.id))
        return Response(self.get_serializer(post).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """Saca una publicacion programada de la cola (queda guardada como borrador)."""
        tomada = StoryPost.objects.filter(pk=pk, estado=StoryPost.Estado.PROGRAMADA).update(
            estado=StoryPost.Estado.BORRADOR, programada_para=None, actualizado=timezone.now()
        )
        if not tomada:
            return Response(
                {"detail": "Ya no está programada: puede que se haya empezado a publicar."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=False, methods=["get"])
    def registro(self, request):
        """Lo que se ve hoy en Instagram y las ultimas publicaciones (con sus errores)."""
        hace_un_dia = timezone.now() - timezone.timedelta(hours=24)
        en_instagram = StoryPost.objects.filter(
            formato=StoryPost.Formato.HISTORIA, estado=StoryPost.Estado.PUBLICADA, publicado_en__gte=hace_un_dia
        ).order_by("-publicado_en")
        programadas = StoryPost.objects.filter(estado=StoryPost.Estado.PROGRAMADA).order_by("programada_para")
        recientes = StoryPost.objects.exclude(
            estado__in=[StoryPost.Estado.BORRADOR, StoryPost.Estado.PROGRAMADA]
        ).order_by("-actualizado")[:20]
        contexto = self.get_serializer_context()
        return Response(
            {
                "en_instagram": StoryPostSerializer(en_instagram, many=True, context=contexto).data,
                "programadas": StoryPostSerializer(programadas, many=True, context=contexto).data,
                "recientes": StoryPostSerializer(recientes, many=True, context=contexto).data,
            }
        )

    @action(detail=False, methods=["post"])
    def sugerir_texto(self, request):
        entrada = SugerirTextoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            resultado = ai_copy.sugerir_texto(**entrada.validated_data)
        except ai_copy.AICopyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(resultado)


class RepeticionViewSet(viewsets.ModelViewSet):
    """Historias que se vuelven a publicar solas cada tantos dias."""

    queryset = Repeticion.objects.select_related("historia")
    serializer_class = RepeticionSerializer
