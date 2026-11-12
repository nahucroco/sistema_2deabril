from django.contrib import admin

from .models import InstagramAccount, StoryPost


@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ig_user_id", "activa", "token_expires_at", "token_por_vencer")
    readonly_fields = ("creado",)

    @admin.display(boolean=True, description="Token por vencer (<7 dias)")
    def token_por_vencer(self, obj):
        return obj.token_por_vencer


@admin.register(StoryPost)
class StoryPostAdmin(admin.ModelAdmin):
    list_display = ("id", "tipo", "titulo", "estado", "cuenta", "programada_para", "publicado_en")
    list_filter = ("estado", "tipo", "cuenta")
    readonly_fields = ("ig_container_id", "ig_media_id", "error_mensaje", "creado", "actualizado", "publicado_en")
    search_fields = ("titulo", "detalle", "caption")
