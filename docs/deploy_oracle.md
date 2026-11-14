# Deploy gratis en Oracle Cloud (Always Free)

Todo corre en una sola máquina virtual gratis, con Docker Compose:

```
Internet ──HTTPS──> Caddy ──┬── /panel ────────> el Taller de Historias (React compilado)
                            ├── /media ────────> fotos (Meta descarga las historias de acá)
                            ├── /static ───────> CSS de la web y archivos del admin
                            └── resto ─────────> Django (gunicorn): web pública, /api, /admin ──> Postgres
                 "tareas": cada 5 min publica las programadas y destraba las colgadas
```

No hace falta Redis ni Celery: "Publicar ahora" publica en el mismo pedido.

Los planes gratuitos cambian; si algo de lo que sigue no coincide con lo que
muestra Oracle, la idea es la misma.

## 1. Crear la cuenta en Oracle Cloud

1. Entrá a https://www.oracle.com/cloud/free/ → **Start for free**.
2. **Home region**: elegí la más cercana (por ejemplo *Brazil East (São
   Paulo)* o *Chile Central (Santiago)*). **No se puede cambiar después**, y
   las máquinas gratis solo se crean en esa región.
3. Te pide una tarjeta para verificar la identidad. No cobra mientras uses
   solo recursos "Always Free".

> **Ojo:** Oracle puede recuperar máquinas *Always Free* que pasan muchos
> días casi sin uso. Si te pasa, o para evitarlo, podés pasar la cuenta a
> **Pay As You Go** (Billing → Upgrade): seguís sin pagar mientras no salgas
> de los límites gratis, y no te reclaman la máquina. Poné una alerta de
> presupuesto en USD 1 por las dudas.

## 2. Crear la máquina virtual

Menú ☰ → **Compute → Instances → Create instance**.

- **Name:** `sistema-2deabril`
- **Image:** *Canonical Ubuntu 24.04* (Change image → Ubuntu).
- **Shape:** Change shape → **Ampere** → `VM.Standard.A1.Flex`,
  **2 OCPU y 12 GB** de memoria (el límite gratis es 4 OCPU / 24 GB en total).
- **Networking:** dejá que cree la red (VCN) nueva y marcá **Assign a public
  IPv4 address**.
- **SSH keys:** **Generate a key pair for me** → descargá la **private key**
  y guardala bien (sin ella no podés entrar a la máquina).
- **Boot volume:** el default (≈50 GB) alcanza.

**Create**. Si dice *Out of capacity*, probá otro *Availability domain* o
volvé a intentar más tarde: pasa seguido con las máquinas Ampere gratis.

Cuando quede en verde (*Running*), anotá la **Public IP address**.

## 3. Abrir los puertos 80 y 443

Oracle tiene dos firewalls; hay que abrir los dos.

**a) En el panel de Oracle:** en la instancia → la **Subnet** → la
**Default Security List** → **Add Ingress Rules**, dos reglas:

| Source CIDR | IP Protocol | Destination Port |
|-------------|-------------|------------------|
| `0.0.0.0/0` | TCP         | `80`             |
| `0.0.0.0/0` | TCP         | `443`            |

**b) Dentro de la máquina** (lo hacés en el paso 5, ya conectado por SSH).

## 4. Conseguir el dominio gratis (DuckDNS)

1. Entrá a https://www.duckdns.org e iniciá sesión (con Google o GitHub).
2. Creá un subdominio, por ejemplo `bici2deabril` → queda
   `bici2deabril.duckdns.org`.
3. En **current ip** poné la IP pública de la máquina → **update ip**.

## 5. Preparar la máquina

Desde PowerShell en tu compu (cambiá la ruta de la clave y la IP):

```bash
ssh -i C:\ruta\a\ssh-key.key ubuntu@IP_PUBLICA
```

Si Windows se queja de permisos de la clave: clic derecho en el archivo →
Propiedades → Seguridad → Opciones avanzadas → deshabilitar herencia y
dejar solo a tu usuario.

Ya adentro, abrí los puertos en el firewall de Ubuntu:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Instalá Docker:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
exit
```

(Volvé a entrar por SSH para que tome el grupo `docker`.)

## 6. Bajar el proyecto y configurarlo

```bash
git clone https://github.com/nahucroco/sistema_2deabril.git
cd sistema_2deabril
cp deploy/.env.prod.example .env.prod
```

Generá dos claves y copialas:

```bash
openssl rand -hex 24   # -> POSTGRES_PASSWORD
openssl rand -hex 50   # -> SECRET_KEY
```

Editá el archivo y completá `DOMAIN` (ej. `bici2deabril.duckdns.org`, sin
`https://`), `POSTGRES_PASSWORD` y `SECRET_KEY`:

```bash
nano .env.prod      # Ctrl+O, Enter para guardar; Ctrl+X para salir
```

## 7. Levantar todo

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

La primera vez tarda unos minutos (compila el frontend y las dependencias).
Para ver que todo esté arriba:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f caddy backend
```

Abrí `https://TU_DOMINIO/panel/` en el navegador: tiene que aparecer la pantalla
de login con el candadito de HTTPS. Si Caddy no consigue el certificado,
revisá que DuckDNS apunte a la IP correcta y que los puertos 80/443 estén
abiertos (paso 3).

## 8. Crear el usuario y conectar Instagram

Para no escribir el comando largo cada vez:

```bash
alias dc='docker compose -f docker-compose.prod.yml --env-file .env.prod'
```

Usuario para entrar al Taller (y al `/admin/`):

```bash
dc exec backend python manage.py createsuperuser
```

Conectar la cuenta de Instagram con el token del panel de Meta (lo pide
oculto, ver `docs/instagram_setup.md`):

```bash
dc exec backend python manage.py conectar_instagram
```

Listo:

- `https://TU_DOMINIO` es la web pública para los clientes.
- `https://TU_DOMINIO/panel/` es el Taller de Historias (pide login).
- `https://TU_DOMINIO/admin/` → "Web pública": productos, servicios del taller
  y datos del negocio (WhatsApp, dirección, horarios).

## Mantenimiento

**Actualizar a la última versión del código:**

```bash
cd ~/sistema_2deabril && git pull
dc up -d --build
```

**Backup de la base** (conviene bajarlo a tu compu de vez en cuando):

```bash
dc exec -T db pg_dump -U sistema sistema_2deabril | gzip > backup-$(date +%F).sql.gz
```

**Ver errores:** `dc logs --tail 100 backend tareas`

**Si cambia la IP de la máquina** (no debería, salvo que la borres): hay que
actualizarla en DuckDNS.
