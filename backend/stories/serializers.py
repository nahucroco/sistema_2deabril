from rest_framework import serializers

from .models import InstagramAccount, StoryPost


class InstagramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramAccount
        fields = ["id", "nombre", "ig_user_id", "activa", "token_expires_at"]
        # access_token nunca se expone por API.


class StoryPostSerializer(serializers.ModelSerializer):
    imagen_url_publica = serializers.ReadOnlyField()

    class Meta:
        model = StoryPost
        fields = [
            "id",
            "cuenta",
            "tipo",
            "imagen",
            "imagen_url_publica",
            "titulo",
            "detalle",
            "precio",
            "caption",
            "estado",
            "programada_para",
            "ig_container_id",
            "ig_media_id",
            "error_mensaje",
            "creado",
            "actualizado",
            "publicado_en",
        ]
        read_only_fields = [
            "estado",
            "ig_container_id",
            "ig_media_id",
            "error_mensaje",
            "creado",
            "actualizado",
            "publicado_en",
        ]


class SugerirTextoSerializer(serializers.Serializer):
    """Entrada para el endpoint que pide a Claude titulos/detalle/caption."""

    idea = serializers.CharField(max_length=600)
    tipo = serializers.ChoiceField(choices=StoryPost.Tipo.choices)
