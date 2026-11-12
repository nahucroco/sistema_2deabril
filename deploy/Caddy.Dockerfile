# Compila el frontend y lo empaqueta con Caddy. Se construye desde la raiz del repo.
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend /frontend/dist /srv/frontend
