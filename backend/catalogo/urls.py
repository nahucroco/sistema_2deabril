from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import PaginasSitemap, ProductosSitemap

app_name = "catalogo"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("producto/<slug:slug>/", views.producto, name="producto"),
    path("taller/", views.taller, name="taller"),
    path("robots.txt", views.robots, name="robots"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"paginas": PaginasSitemap, "productos": ProductosSitemap}},
        name="sitemap",
    ),
]
