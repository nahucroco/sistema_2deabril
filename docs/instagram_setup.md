# Conectar la cuenta de Instagram del local

Esto hay que hacerlo una sola vez, a mano. No hay forma de automatizarlo
por API: Meta exige que estos pasos se hagan desde la interfaz, con el
dueño de la cuenta.

## 1. Pasar la cuenta a profesional, tipo Empresa

1. Abrí Instagram desde el celular con la cuenta del local.
2. Configuración → Cuenta → Cambiar a cuenta profesional.
3. Elegí **Empresa** (no "Creador": la API de publicación de contenido no
   funciona de forma confiable con cuentas de Creador — mejor evitar esa
   confusión directamente).
4. Si todavía no existe, te va a pedir vincular una **página de Facebook**.
   Podés crear una página nueva solo para esto, no hace falta que el local
   la use activamente.

## 2. Crear la app en Meta for Developers

1. Entrá a https://developers.facebook.com/apps y creá una app nueva, tipo
   "Business".
2. Dentro de la app, agregá el producto **Instagram** (Instagram API with
   Instagram Login, o el flujo equivalente que te muestre el panel —
   Meta lo reordena de tanto en tanto).
3. Anotá el **App ID** y el **App Secret**: van en el `.env` del backend
   (`META_APP_ID`, `META_APP_SECRET`).

## 3. Conectar la cuenta y generar el token

1. En el panel de la app, usá el flujo de login/autorización para conectar
   la cuenta de Instagram del local y pedir los permisos:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
2. Mientras la app esté en **modo desarrollo** y solo la uses para la
   cuenta del local (no para cuentas de terceros), no hace falta pasar por
   App Review.
3. Al final de ese flujo vas a tener:
   - El **Instagram Business Account ID** (el `ig_user_id`, no es el @usuario).
   - Un **access token de larga duración** (dura 60 días).

## 4. Cargar la cuenta en el sistema

No se carga por la app web: se hace una sola vez desde el admin de Django,
para no tener el token dando vueltas por la interfaz.

1. Entrá a `/admin/` con un usuario con permisos de staff.
2. Stories → Cuentas de Instagram → Agregar.
3. Completá `nombre`, `ig_user_id`, `access_token` y `token_expires_at`
   (hoy + 60 días).

De ahí en adelante, la tarea periódica `refresh_expiring_tokens` (Celery
beat, corre una vez por día) renueva el token automáticamente cuando le
quedan menos de 7 días — mientras el servidor esté corriendo. Si el token
llega a vencer sin renovarse, hay que repetir el paso 3 y volver a cargarlo
a mano.

## Límites a tener en cuenta

- 100 publicaciones por API cada 24 horas móviles, contando historias,
  posts y reels juntos.
- La API no permite agregar stickers interactivos a las historias
  (encuestas, links, menciones, música, cuenta regresiva): todo el texto
  y el contacto van dibujados en la imagen, que es justo lo que hace el
  Taller de Historias.
- Las historias vencen a las 24 horas; no hay forma de extenderlas por API.
