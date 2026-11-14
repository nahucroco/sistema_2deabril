from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import DatosNegocio, Producto, ServicioTaller

# Los que no tienen precio ("Consultar") van al final en los dos sentidos.
ORDENES = {
    "nuevos": ("Más nuevos", ["-creado"]),
    "menor": ("Menor precio", [F("precio").asc(nulls_last=True), "-creado"]),
    "mayor": ("Mayor precio", [F("precio").desc(nulls_last=True), "-creado"]),
}
POR_PAGINA = 24


def _con_fotos(qs):
    return qs.prefetch_related("fotos")


@require_GET
def inicio(request):
    en_catalogo = _con_fotos(Producto.objects.en_catalogo())
    destacados = list(en_catalogo.filter(destacado=True)[:8])
    if not destacados:  # si no marcaron ninguno, mostramos los ultimos
        destacados = list(en_catalogo[:4])
    return render(request, "catalogo/inicio.html", {"destacados": destacados})


@require_GET
def catalogo(request):
    qs = Producto.objects.en_catalogo()

    categoria = request.GET.get("categoria", "")
    if categoria not in Producto.Categoria.values:
        categoria = ""
    if categoria:
        qs = qs.filter(categoria=categoria)

    # Los rodados del filtro salen de lo que hay (con la categoria elegida).
    rodados = sorted(set(qs.exclude(rodado=None).values_list("rodado", flat=True)))

    rodado = request.GET.get("rodado", "")
    if rodado.isdigit() and int(rodado) in rodados:
        qs = qs.filter(rodado=int(rodado))
    else:
        rodado = ""

    buscar = request.GET.get("q", "").strip()[:80]
    if buscar:
        qs = qs.filter(Q(nombre__icontains=buscar) | Q(detalle__icontains=buscar) | Q(descripcion__icontains=buscar))

    orden = request.GET.get("orden", "nuevos")
    if orden not in ORDENES:
        orden = "nuevos"
    qs = qs.order_by(*ORDENES[orden][1])

    pagina = Paginator(_con_fotos(qs), POR_PAGINA).get_page(request.GET.get("pagina"))

    # Para armar los links de paginas sin perder los filtros.
    filtros = request.GET.copy()
    filtros.pop("pagina", None)

    return render(
        request,
        "catalogo/catalogo.html",
        {
            "pagina": pagina,
            "categorias": [("", "Todo")] + list(Producto.Categoria.choices),
            "categoria": categoria,
            "rodados": rodados,
            "rodado": rodado,
            "ordenes": [(clave, nombre) for clave, (nombre, _) in ORDENES.items()],
            "orden": orden,
            "buscar": buscar,
            "filtros": filtros.urlencode(),
        },
    )


@require_GET
def producto(request, slug):
    item = get_object_or_404(_con_fotos(Producto.objects.publicos()), slug=slug)
    relacionados = _con_fotos(
        Producto.objects.en_catalogo().filter(categoria=item.categoria).exclude(pk=item.pk)
    )[:4]
    url = request.build_absolute_uri(item.get_absolute_url())
    negocio = DatosNegocio.actual()
    return render(
        request,
        "catalogo/producto.html",
        {
            "producto": item,
            "fotos": list(item.fotos.all()),
            "relacionados": relacionados,
            "url_absoluta": url,
            "whatsapp_producto": negocio.link_whatsapp(f"¡Hola! Me interesa «{item.nombre}», que vi en la web: {url}"),
        },
    )


@require_GET
def taller(request):
    return render(request, "catalogo/taller.html", {"servicios": ServicioTaller.objects.filter(activo=True)})


@require_GET
def robots(request):
    lineas = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /panel/",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lineas) + "\n", content_type="text/plain")
