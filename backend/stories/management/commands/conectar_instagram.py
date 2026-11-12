"""
Carga (o actualiza) la cuenta de Instagram del local a partir de un token
de Unified login generado en el panel de Meta.

El token se pide por teclado sin mostrarlo, para que no quede en el
historial de la terminal ni haya que pegarlo en ningun otro lado:

    python manage.py conectar_instagram

Busca solo el ID de la cuenta de Instagram que tiene asignada el token y
comprueba que funcione antes de guardarlo.
"""

from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from stories.models import InstagramAccount
from stories.services import meta_graph


class Command(BaseCommand):
    help = "Conecta la cuenta de Instagram del local usando el token generado en el panel de Meta."

    def add_arguments(self, parser):
        parser.add_argument("--nombre", default="2 de Abril", help="Como se va a ver la cuenta en el admin.")
        parser.add_argument(
            "--ig-user-id",
            help="ID de la cuenta de Instagram, si el token tiene varias asignadas o no se puede averiguar solo.",
        )

    def handle(self, *args, nombre, ig_user_id, **options):
        token = getpass("Pegá el token de acceso (no se va a ver mientras lo pegás) y apretá Enter: ").strip()
        if not token:
            raise CommandError("No se ingresó ningún token.")

        if not ig_user_id:
            ig_user_id = self._averiguar_cuenta(token)

        try:
            datos = meta_graph.datos_cuenta(ig_user_id, token)
        except meta_graph.GraphAPIError as exc:
            raise CommandError(f"El token no funciona con la cuenta {ig_user_id}: {exc}") from exc

        cuenta, creada = InstagramAccount.objects.update_or_create(
            ig_user_id=ig_user_id,
            defaults={
                "nombre": nombre,
                "access_token": token,
                # Los tokens de usuario del sistema de Unified login no vencen.
                "token_expires_at": None,
                "activa": True,
            },
        )
        accion = "Conectada" if creada else "Actualizada"
        self.stdout.write(
            self.style.SUCCESS(f"{accion}: @{datos.get('username', '?')} (ID {cuenta.ig_user_id}) como '{cuenta.nombre}'.")
        )

    def _averiguar_cuenta(self, token: str) -> str:
        try:
            cuentas = meta_graph.cuentas_instagram_asignadas(token)
        except meta_graph.GraphAPIError as exc:
            raise CommandError(
                f"No se pudo consultar qué cuenta de Instagram tiene el token: {exc}\n"
                "Revisá que el token esté completo, o pasá el ID a mano con --ig-user-id."
            ) from exc

        if not cuentas:
            raise CommandError(
                "El token no tiene ninguna cuenta de Instagram asignada. "
                "Revisá en el panel de Meta que la configuración incluya la cuenta del local."
            )
        if len(cuentas) > 1:
            lista = "\n".join(f"  {c['id']}  @{c.get('username', '?')}" for c in cuentas)
            raise CommandError(f"El token tiene varias cuentas; elegí una con --ig-user-id:\n{lista}")
        return cuentas[0]["id"]
