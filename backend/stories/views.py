from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import InstagramAccount, StoryPost
from .serializers import (
    InstagramAccountSerializer,
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
        publicar_post.delay(post.id)
        post.estado = StoryPost.Estado.PUBLICANDO
        post.save(update_fields=["estado"])
        return Response(self.get_serializer(post).data)

    @action(detail=False, methods=["post"])
    def sugerir_texto(self, request):
        entrada = SugerirTextoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        try:
            resultado = ai_copy.sugerir_texto(**entrada.validated_data)
        except ai_copy.AICopyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(resultado)
