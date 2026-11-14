# Sistema 2 de Abril

Herramienta de marketing para la Bicicletería 2 de Abril: un taller donde
se elige una foto, se arma una historia para Instagram con la identidad
del local y un texto sugerido, y se publica (o se guarda para subir a
mano) — sin que haga falta saber nada de diseño ni de redes.

## Por qué existe

El dueño del local maneja bien Marketplace para comprar y vender, pero no
tiene tiempo ni ganas de pelearse con ediciones de fotos para Instagram.
Esta app resuelve un solo problema primero (las historias) para que la
use de verdad, y después se le van sumando otras cosas según lo que
realmente le haga falta (ver "Ideas para después" más abajo).

## Estructura del repo

```
backend/    Django + DRF + Celery: modelos, API REST, publicación a
            Instagram vía Graph API, tareas programadas (publicar
            historias programadas, renovar el token cada 60 días).
            La app "catalogo" es la web pública (templates de Django).
frontend/   React (Vite), en /panel/: el flujo de 4 pasos (foto → tipo de
            publicación → texto → guardar/publicar), con vista previa
            9:16 en <canvas> que reusa el diseño validado en el
            prototipo.
docs/       Guías, entre ellas instagram_setup.md: cómo pasar la cuenta
            a Empresa y conectar la app de Meta (son pasos manuales,
            no se pueden hacer por API).
```

## Arrancar en desarrollo

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar ANTHROPIC_API_KEY como mínimo, para el paso 3
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Para publicar de verdad a Instagram hace falta además Redis (Celery) y
seguir `docs/instagram_setup.md` para cargar la cuenta desde `/admin/`.
Sin eso, el Taller funciona igual para guardar la imagen como PNG.

```bash
# en otra terminal, con el venv activado
celery -A config worker -l info
celery -A config beat -l info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

El Taller de Publicaciones abre en `http://localhost:5173/panel/`. En desarrollo,
Vite proxea `/api`, `/admin`, `/static` y `/media` hacia
`http://localhost:8000` (el backend de Django).

### Web pública

La sirve Django: `http://localhost:8000/` (inicio), `/catalogo/`,
`/producto/<slug>/` y `/taller/`. Los productos, los servicios del taller y
los datos de contacto (WhatsApp, dirección, horarios) se cargan desde
`/admin/`, en la sección "Web pública". La web no cobra: cada producto
lleva a WhatsApp con el mensaje armado y, si tiene, a su publicación de
Mercado Libre o Marketplace.

### Produccion

Deploy gratis en Oracle Cloud con Docker Compose + Caddy (HTTPS automatico):
ver `docs/deploy_oracle.md`.

### Con Docker (desarrollo)

```bash
cp backend/.env.example backend/.env   # completar antes de levantar
docker compose up --build
```

## Estado actual

- [x] Taller de historias: foto, plantillas de marca, texto sugerido con
      Claude, descarga en PNG.
- [x] Backend con el modelo de datos y la integración con la Graph API de
      Meta lista para publicar y programar.
- [x] Cuenta real del local conectada (Unified login, ver `docs/instagram_setup.md`)
      y primera historia publicada por API.
- [x] Login para usar el Taller en produccion.
- [x] Deploy en una VM gratis (Google Cloud e2-micro; guía en `docs/deploy_oracle.md`).
- [x] Web pública: inicio, catálogo con filtros, ficha de producto con
      WhatsApp y Mercado Libre, página del taller. Se administra desde `/admin/`.
- [ ] Sección de productos dentro del panel y "crear historia desde un producto".
- [x] Posts del feed (4:5): publicar ahora o programados, con texto propio.
- [x] Historias que se repiten solas y registro de publicaciones.
- [ ] Reels.
- [ ] Bandeja de comentarios/mensajes de Instagram con respuestas sugeridas.

## Ideas para después

Pensadas para no agregar nada que el dueño no vaya a usar; conviene
confirmar con él cuál le resuelve más antes de construirla:

- Gestión de taller: bicis que entran a reparar, con aviso por WhatsApp
  al cliente cuando están listas.
- Recordatorios de service a los 6 meses de una venta o reparación.
- Perfil de Google Maps: reseñas y respuestas sugeridas.
- Catálogo único que alimente Instagram, Marketplace y Mercado Libre a
  la vez.
- Links de pago de Mercado Pago para señas o reservas.
