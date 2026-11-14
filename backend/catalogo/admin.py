from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from .models import DatosNegocio, FotoProducto, Producto, ServicioTaller

admin.site.site_header = "Bicicletería 2 de Abril"
admin.site.site_title = "2 de Abril"
admin.site.index_title = "Administración"
admin.site.site_url = "/"


class FotoInline(admin.TabularInline):
    model = FotoProducto
    extra = 1
    fields = ("vista", "imagen", "orden")
    readonly_fields = ("vista",)

    @admin.display(description="Vista previa")
    def vista(self, obj):
        if not obj.imagen:
            return "—"
        return format_html('<img src="{}" style="height:70px;border-radius:6px">', obj.imagen.url)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio", "estado", "destacado", "actualizado")
    list_editable = ("precio", "estado", "destacado")
    list_filter = ("estado", "categoria", "destacado")
    search_fields = ("nombre", "detalle", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [FotoInline]
    fieldsets = (
        (None, {"fields": ("nombre", "categoria", "estado", "destacado")}),
        ("Precio", {"fields": ("precio", "precio_anterior")}),
        ("Descripción", {"fields": ("detalle", "descripcion", "caracteristicas", "rodado")}),
        ("Dónde comprarlo", {"fields": ("link_mercadolibre", "link_marketplace")}),
        ("Avanzado", {"fields": ("slug",), "classes": ("collapse",)}),
    )
    actions = ["marcar_vendido", "marcar_disponible"]

    def view_on_site(self, obj):
        return obj.get_absolute_url()

    @admin.action(description="Marcar como vendidos")
    def marcar_vendido(self, request, queryset):
        queryset.update(estado=Producto.Estado.VENDIDO)

    @admin.action(description="Marcar como disponibles")
    def marcar_disponible(self, request, queryset):
        queryset.update(estado=Producto.Estado.DISPONIBLE)


@admin.register(ServicioTaller)
class ServicioTallerAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "orden", "activo")
    list_editable = ("precio", "orden", "activo")


@admin.register(DatosNegocio)
class DatosNegocioAdmin(admin.ModelAdmin):
    """Un solo registro: la lista lleva directo al formulario."""

    def changelist_view(self, request, extra_context=None):
        obj = DatosNegocio.actual()
        return redirect(reverse("admin:catalogo_datosnegocio_change", args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
