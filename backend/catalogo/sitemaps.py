from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Producto


class PaginasSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return ["catalogo:inicio", "catalogo:catalogo", "catalogo:taller"]

    def location(self, item):
        return reverse(item)


class ProductosSitemap(Sitemap):
    changefreq = "daily"

    def items(self):
        return Producto.objects.en_catalogo()

    def lastmod(self, obj):
        return obj.actualizado
