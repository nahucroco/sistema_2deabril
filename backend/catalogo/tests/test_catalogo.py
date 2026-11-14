import io
from urllib.parse import parse_qs, urlparse

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from catalogo.models import DatosNegocio, FotoProducto, Producto, ServicioTaller, formatear_pesos
from stories.tests.helpers import MediaTemporalMixin


def crear_producto(**kwargs):
    datos = {"nombre": "Vairo XR 3.5 R29", "categoria": Producto.Categoria.USADA, "precio": 450000}
    datos.update(kwargs)
    return Producto.objects.create(**datos)


def foto_subida(ancho=3000, alto=2000, formato="JPEG", modo="RGB", nombre="foto.jpg"):
    buffer = io.BytesIO()
    Image.new(modo, (ancho, alto), color=(20, 60, 140, 0) if modo == "RGBA" else (20, 60, 140)).save(
        buffer, format=formato
    )
    return SimpleUploadedFile(nombre, buffer.getvalue())


class ModelosTests(TestCase):
    def test_slug_se_genera_y_no_se_repite(self):
        a = crear_producto(nombre="Casco urbano")
        b = crear_producto(nombre="Casco urbano")
        self.assertEqual(a.slug, "casco-urbano")
        self.assertEqual(b.slug, "casco-urbano-2")

    def test_formato_de_precio(self):
        self.assertEqual(formatear_pesos(450000), "$ 450.000")
        self.assertEqual(crear_producto(precio=None).precio_texto, "Consultar")

    def test_oferta_solo_si_el_precio_anterior_es_mayor(self):
        oferta = crear_producto(precio=160000, precio_anterior=190000)
        self.assertEqual(oferta.etiqueta, ("Oferta", "oferta"))
        self.assertEqual(oferta.precio_anterior_texto, "$ 190.000")
        raro = crear_producto(precio=200000, precio_anterior=150000)
        self.assertEqual(raro.etiqueta, ("Usada", "usada"))
        self.assertEqual(raro.precio_anterior_texto, "")

    def test_caracteristicas_por_renglon(self):
        p = crear_producto(caracteristicas="Rodado: 29\n\nFrenos: a disco\nCon luces")
        self.assertEqual(p.lista_caracteristicas, [("Rodado", "29"), ("Frenos", "a disco"), ("", "Con luces")])

    def test_datos_negocio_es_unico_y_limpia_el_whatsapp(self):
        DatosNegocio(whatsapp="1").save()
        DatosNegocio(whatsapp="+54 9 341 555-1234", instagram="@bici").save()  # pisa el mismo registro
        self.assertEqual(DatosNegocio.objects.count(), 1)
        datos = DatosNegocio.actual()
        self.assertEqual(datos.whatsapp, "5493415551234")
        self.assertEqual(datos.instagram, "bici")
        datos.delete()
        self.assertEqual(DatosNegocio.objects.count(), 1)

    def test_link_de_whatsapp_codifica_el_texto(self):
        datos = DatosNegocio(whatsapp="5493415551234")
        url = urlparse(datos.link_whatsapp("Hola & chau"))
        self.assertEqual(url.netloc, "wa.me")
        self.assertEqual(url.path, "/5493415551234")
        self.assertEqual(parse_qs(url.query)["text"], ["Hola & chau"])
        self.assertEqual(DatosNegocio(whatsapp="").link_whatsapp("x"), "")

    def test_servicios_iniciales_de_la_migracion(self):
        self.assertTrue(ServicioTaller.objects.filter(nombre="Service completo").exists())


class FotosTests(MediaTemporalMixin, TestCase):
    def test_achica_y_pasa_a_jpeg(self):
        foto = FotoProducto.objects.create(producto=crear_producto(), imagen=foto_subida(4000, 3000))
        with Image.open(foto.imagen.path) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(max(img.size), 1600)

    def test_png_con_transparencia_queda_con_fondo_blanco(self):
        foto = FotoProducto.objects.create(
            producto=crear_producto(), imagen=foto_subida(100, 100, "PNG", "RGBA", "logo.png")
        )
        self.assertTrue(foto.imagen.name.endswith(".jpg"))
        with Image.open(foto.imagen.path) as img:
            self.assertEqual(img.getpixel((50, 50)), (255, 255, 255))

    def test_editar_sin_cambiar_la_foto_no_la_reprocesa(self):
        foto = FotoProducto.objects.create(producto=crear_producto(), imagen=foto_subida(800, 600))
        nombre = foto.imagen.name
        foto.orden = 3
        foto.save()
        self.assertEqual(foto.imagen.name, nombre)


class PaginasTests(MediaTemporalMixin, TestCase):
    def setUp(self):
        datos = DatosNegocio.actual()
        datos.whatsapp = "5493415551234"
        datos.direccion = "San Martín 123, Rosario"
        datos.horarios = "Lunes a viernes: 9 a 18 h"
        datos.save()

    def test_inicio_muestra_destacados_y_datos(self):
        crear_producto(nombre="Bici destacada", destacado=True)
        crear_producto(nombre="Bici comun")
        r = self.client.get(reverse("catalogo:inicio"))
        self.assertContains(r, "Bici destacada")
        self.assertNotContains(r, "Bici comun")
        self.assertContains(r, "San Martín 123, Rosario")
        self.assertContains(r, "https://wa.me/5493415551234")

    def test_inicio_sin_destacados_muestra_los_ultimos(self):
        crear_producto(nombre="Bici comun")
        self.assertContains(self.client.get(reverse("catalogo:inicio")), "Bici comun")

    def test_catalogo_no_lista_vendidos_ni_ocultos(self):
        crear_producto(nombre="Disponible")
        crear_producto(nombre="Reservada", estado=Producto.Estado.RESERVADO)
        crear_producto(nombre="Vendida", estado=Producto.Estado.VENDIDO)
        crear_producto(nombre="Oculta", estado=Producto.Estado.OCULTO)
        r = self.client.get(reverse("catalogo:catalogo"))
        self.assertContains(r, "Disponible")
        self.assertContains(r, "Reservada")
        self.assertNotContains(r, "Vendida")
        self.assertNotContains(r, "Oculta")

    def test_filtros_del_catalogo(self):
        crear_producto(nombre="Mountain R29", categoria=Producto.Categoria.NUEVA, rodado=29, precio=600000)
        crear_producto(nombre="Urbana R26", categoria=Producto.Categoria.NUEVA, rodado=26, precio=300000)
        crear_producto(nombre="Casco", categoria=Producto.Categoria.ACCESORIO, precio=None)
        url = reverse("catalogo:catalogo")

        r = self.client.get(url, {"categoria": "nueva", "rodado": "26"})
        self.assertEqual([p.nombre for p in r.context["pagina"]], ["Urbana R26"])

        r = self.client.get(url, {"q": "casco"})
        self.assertEqual([p.nombre for p in r.context["pagina"]], ["Casco"])

        r = self.client.get(url, {"orden": "menor"})
        self.assertEqual([p.nombre for p in r.context["pagina"]], ["Urbana R26", "Mountain R29", "Casco"])

        # Valores raros no rompen la pagina: se ignoran.
        r = self.client.get(url, {"categoria": "<script>", "rodado": "abc", "orden": "x", "pagina": "999"})
        self.assertEqual(r.status_code, 200)

    def test_el_boton_de_categoria_gana_sobre_el_filtro_anterior(self):
        crear_producto(nombre="Casco", categoria=Producto.Categoria.ACCESORIO)
        crear_producto(nombre="Cubierta", categoria=Producto.Categoria.REPUESTO)
        # Asi llega el formulario: primero el oculto con la categoria actual y despues el boton tocado.
        r = self.client.get(reverse("catalogo:catalogo") + "?categoria=accesorio&categoria=repuesto")
        self.assertEqual([p.nombre for p in r.context["pagina"]], ["Cubierta"])

    def test_ficha_con_whatsapp_y_vista_previa(self):
        p = crear_producto(link_mercadolibre="https://articulo.mercadolibre.com.ar/MLA-1")
        FotoProducto.objects.create(producto=p, imagen=foto_subida(800, 600))
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, "$ 450.000")
        self.assertContains(r, "https://articulo.mercadolibre.com.ar/MLA-1")
        mensaje = parse_qs(urlparse(r.context["whatsapp_producto"]).query)["text"][0]
        self.assertIn("Vairo XR 3.5 R29", mensaje)
        self.assertIn(f"http://testserver{p.get_absolute_url()}", mensaje)
        self.assertContains(r, 'property="og:image" content="http://testserver/media/productos/')

    def test_ficha_de_vendido_se_abre_pero_sin_link_de_compra(self):
        p = crear_producto(estado=Producto.Estado.VENDIDO, link_mercadolibre="https://articulo.mercadolibre.com.ar/MLA-1")
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, "ya se vendió")
        self.assertNotContains(r, "MLA-1")

    def test_ficha_de_oculto_da_404(self):
        p = crear_producto(estado=Producto.Estado.OCULTO)
        self.assertEqual(self.client.get(p.get_absolute_url()).status_code, 404)

    def test_sin_whatsapp_no_hay_botones_rotos(self):
        datos = DatosNegocio.actual()
        datos.whatsapp = ""
        datos.save()
        p = crear_producto()
        r = self.client.get(p.get_absolute_url())
        self.assertNotContains(r, "wa.me")

    def test_taller_lista_servicios_activos(self):
        ServicioTaller.objects.create(nombre="Servicio retirado", activo=False)
        r = self.client.get(reverse("catalogo:taller"))
        self.assertContains(r, "Service completo")
        self.assertNotContains(r, "Servicio retirado")

    def test_sitemap_y_robots(self):
        p = crear_producto()
        crear_producto(nombre="Oculta", estado=Producto.Estado.OCULTO)
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(p.get_absolute_url(), sitemap)
        self.assertNotIn("oculta", sitemap)
        robots = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /admin/", robots)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", robots)

    def test_pantallas_del_admin(self):
        from django.contrib.auth.models import User

        self.client.force_login(User.objects.create_superuser("papa", "", "x"))
        p = crear_producto()
        self.assertEqual(self.client.get("/admin/catalogo/producto/").status_code, 200)
        self.assertEqual(self.client.get("/admin/catalogo/producto/add/").status_code, 200)
        self.assertEqual(self.client.get(f"/admin/catalogo/producto/{p.pk}/change/").status_code, 200)
        self.assertEqual(self.client.get("/admin/catalogo/serviciotaller/").status_code, 200)
        # La lista de "Datos del negocio" lleva directo al formulario del unico registro.
        r = self.client.get("/admin/catalogo/datosnegocio/")
        self.assertRedirects(r, "/admin/catalogo/datosnegocio/1/change/")

    def test_la_api_y_el_admin_siguen_en_su_lugar(self):
        self.assertEqual(self.client.get("/api/sesion/").status_code, 200)
        self.assertEqual(self.client.get("/admin/").status_code, 302)  # pide login
