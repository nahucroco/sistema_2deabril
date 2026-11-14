from rest_framework import serializers

from django.utils import timezone

from .models import InstagramAccount, Repeticion, StoryPost


class InstagramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramAccount
        fields = ["id", "nombre", "ig_user_id", "activa", "token_expires_at"]
        # access_token nunca se expone por API.


class StoryPostSerializer(serializers.ModelSerializer):
    imagen_url_publica = serializers.ReadOnlyField()
    vence_en = serializers.ReadOnlyField()

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
            "vence_en",
            "repeticion",
        ]
        read_only_fields = [
            "repeticion",
            "estado",
            "ig_container_id",
            "ig_media_id",
            "error_mensaje",
            "creado",
            "actualizado",
            "publicado_en",
        ]


class RepeticionSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(source="historia.imagen", read_only=True)

    class Meta:
        model = Repeticion
        fields = ["id", "historia", "imagen", "nombre", "cada_dias", "hora", "hasta", "activa", "proxima", "ultima", "creado"]
        read_only_fields = ["proxima", "ultima", "creado"]

    def validate_historia(self, historia):
        if self.instance and historia != self.instance.historia:
            raise serializers.ValidationError("No se puede cambiar la historia de una repetición: creá otra.")
        if not historia.imagen:
            raise serializers.ValidationError("La historia no tiene imagen.")
        return historia

    def validate_hasta(self, hasta):
        if hasta and hasta < timezone.localdate():
            raise serializers.ValidationError("La fecha de fin ya pasó.")
        return hasta

    def save(self, **kwargs):
        # El proximo horario se recalcula al crearla, al cambiar dia u hora y al reanudarla.
        datos = self.validated_data
        recalcular = self.instance is None or any(
            campo in datos and datos[campo] != getattr(self.instance, campo) for campo in ("cada_dias", "hora")
        ) or (datos.get("activa") and not self.instance.activa)
        if self.instance is None and not datos.get("nombre"):
            datos["nombre"] = datos["historia"].titulo[:80]
        rep = super().save(**kwargs)
        if recalcular:
            rep.proxima = rep.primera_desde()
            rep.save(update_fields=["proxima"])
        return rep

    def create(self, validated_data):
        # proxima es obligatoria en la base: va un valor provisorio que save() reemplaza.
        validated_data.setdefault("proxima", timezone.now())
        return super().create(validated_data)


class SugerirTextoSerializer(serializers.Serializer):
    """Entrada para el endpoint que pide a Claude titulos/detalle/caption."""

    idea = serializers.CharField(max_length=600)
    tipo = serializers.ChoiceField(choices=StoryPost.Tipo.choices)
