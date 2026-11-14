from django.db import migrations

# Servicios de arranque para que la pagina del taller no quede vacia.
# Los precios se completan desde el admin.
SERVICIOS = [
    ("Service completo", "Limpieza, engrase, ajuste de frenos y cambios, centrado de ruedas."),
    ("Regulación de frenos", "V-brake o a disco mecánico. Incluye cambio de pastillas si hace falta."),
    ("Regulación de cambios", "Ajuste de descarriladores delantero y trasero."),
    ("Centrado de rueda", "Rueda torcida o con rayos flojos."),
    ("Cambio de cámara o cubierta", "Mano de obra. Tenemos cámaras y cubiertas en el local."),
    ("Armado de bici nueva", "Si la compraste en otro lado, te la armamos y regulamos."),
]


def crear(apps, schema_editor):
    ServicioTaller = apps.get_model("catalogo", "ServicioTaller")
    if ServicioTaller.objects.exists():
        return
    for orden, (nombre, detalle) in enumerate(SERVICIOS, start=1):
        ServicioTaller.objects.create(nombre=nombre, detalle=detalle, orden=orden)


class Migration(migrations.Migration):
    dependencies = [("catalogo", "0001_initial")]

    operations = [migrations.RunPython(crear, migrations.RunPython.noop)]
