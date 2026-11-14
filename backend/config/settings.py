"""
Configuracion de Django para sistema_2deabril.

Variables de entorno: ver .env.example. En local, copia ese archivo a .env
y completa lo que necesites (como minimo SECRET_KEY para produccion).
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env("SECRET_KEY", default="inseguro-solo-para-desarrollo-local")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

if not DEBUG and SECRET_KEY == "inseguro-solo-para-desarrollo-local":
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("En produccion (DEBUG=False) hay que definir SECRET_KEY en el entorno.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "rest_framework",
    "corsheaders",
    "stories",
    "catalogo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "catalogo.context_processors.negocio",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de datos: Postgres si hay DATABASE_URL, si no sqlite para arrancar rapido en desarrollo.
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # En DEBUG permitimos acceso anonimo para poder probar el front sin
    # loguearse. En produccion (DEBUG=False) queda IsAuthenticated: la
    # API maneja tokens de Instagram y plata, no se expone sin login.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny"
        if DEBUG
        else "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Freno a los intentos de adivinar la contraseña en /api/sesion/iniciar/.
    "DEFAULT_THROTTLE_RATES": {"login": "10/min"},
    # Cuantos proxies hay delante de Django (1 con Caddy en produccion), para que el
    # limite de intentos use la IP real del visitante y no la del proxy.
    "NUM_PROXIES": env.int("NUM_PROXIES", default=None),
}

# Detras de Caddy (HTTPS): el proxy avisa por este header que la conexion original era segura.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 dias: el dueño no tiene que loguearse a cada rato

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
# En local, True corre las tareas en el mismo proceso de Django, sin Redis ni worker.
# Las historias programadas igual necesitan Celery beat, asi que eso no anda en este modo.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

# Meta / Instagram Graph API
META_APP_ID = env("META_APP_ID", default="")
META_APP_SECRET = env("META_APP_SECRET", default="")
GRAPH_API_VERSION = env("GRAPH_API_VERSION", default="v27.0")
# URL publica de la carpeta de media (Meta descarga las imagenes de aca).
PUBLIC_MEDIA_BASE_URL = env("PUBLIC_MEDIA_BASE_URL", default="http://localhost:8000/media")

# Anthropic (sugerencias de texto)
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
