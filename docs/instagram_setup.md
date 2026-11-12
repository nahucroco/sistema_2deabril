# Conectar la cuenta de Instagram del local

Se hace una sola vez. Son pasos manuales en Instagram y en el panel de Meta
(no se pueden automatizar), y al final un comando que guarda el token.

La app usa la **API de Instagram con inicio de sesión unificado** (Unified
login): es la única opción que Meta ofrece a las apps nuevas, no necesita
página de Facebook y genera un token que **no vence**.

## 1. Pasar la cuenta a profesional, tipo Negocio

En Instagram: Configuración → Tipo de cuenta y herramientas → Cambiar a
cuenta profesional → **Negocio** (no "Creador"). La página de Facebook es
opcional: se puede saltear.

## 2. Crear la app en Meta for Developers

Hace falta una **cuenta de Facebook** (puede ser la personal de quien
administra el sistema; el Instagram del local se vincula después).

1. https://developers.facebook.com/apps → **Crear app**.
2. Nombre sin las palabras Instagram/Facebook/Meta (ej. "Sistema 2 de Abril").
3. Caso de uso: **Administrar mensajes y contenido en Instagram**.
4. Portfolio comercial: el del local (**Bicicletería 2 de Abril**). Si no
   aparece, desde Meta Business Suite (con la sesión del Instagram) andá a
   Configuración → Usuarios → Personas → Invitar a personas, invitá al correo
   de tu Facebook con control total, aceptá la invitación y volvé a este paso.

## 3. Dar acceso a la cuenta de Instagram

1. En la app: **Roles de la app → Roles → Agregar personas → Evaluador de
   Instagram** → `bicicleteria_2_de_abril`.
2. Con la sesión del Instagram del local, aceptar la invitación en
   https://www.instagram.com/accounts/manage_access/ → **Invitaciones de
   evaluador**.

Mientras la app esté en modo desarrollo y solo se use con la cuenta del
local, no hace falta pasar por App Review.

## 4. Generar el token

**Casos de uso → Personalizar → API setup with Unified login**:

1. **Crear nueva configuración** (valores por defecto; activo: la cuenta de
   Instagram del local). La URL de redireccionamiento se puede dejar vacía.
2. **Generar tokens de acceso** para la cuenta. Copialo y guardalo en un lugar
   seguro: no lo pegues en chats ni en el repo.

## 5. Guardarlo en el sistema

Desde la carpeta `backend` (en local) o con `dc exec backend ...` en el
servidor (ver `docs/deploy_oracle.md`):

```bash
python manage.py conectar_instagram
```

Pide el token sin mostrarlo, averigua solo el ID de la cuenta de Instagram,
comprueba que funcione y lo guarda. Si se genera un token nuevo más adelante,
se vuelve a correr el mismo comando y lo actualiza.

## Para probar publicaciones en local

Meta descarga la imagen de la historia desde internet, así que `localhost` no
le sirve. En local:

1. Servir solo las imágenes: `.venv/Scripts/python scripts/serve_media.py`
   (puerto 8001; no expone la API ni la base).
2. Túnel: `ngrok http 8001`.
3. En `backend/.env`: `PUBLIC_MEDIA_BASE_URL=https://<url-de-ngrok>/media` y
   `CELERY_TASK_ALWAYS_EAGER=True`, y reiniciar el backend.

En producción no hace falta nada de esto: Caddy sirve `/media` en el dominio.

## Límites a tener en cuenta

- 100 publicaciones por API cada 24 horas móviles (historias, posts y reels
  juntos).
- La API no permite stickers interactivos en las historias (encuestas, links,
  menciones, música): todo va dibujado en la imagen, que es lo que hace el
  Taller.
- Las historias vencen a las 24 horas.
