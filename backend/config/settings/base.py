"""
Configuración común a los tres entornos (local, test, production).
Cada entorno hereda de aquí y sólo sobreescribe lo que le corresponde,
conforme a la sección 17 del prompt maestro.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.students",
    "apps.scheduling",
    "apps.attendance",
    "apps.grading",
    "apps.payments",
    "apps.documents",
    "apps.communication",
    "apps.reports",
]

# Sin django.contrib.sessions ni django.contrib.admin: la API es sin estado
# (JWT) y los tres portales son la única interfaz de administración prevista
# (sección 2 del prompt maestro) — no se expone un panel de Django aparte.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.PoliticaDeSeguridadDeContenidoMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.core.validators.ContrasenaComunEsValidator"},
]

LANGUAGE_CODE = "es-gt"
TIME_ZONE = "America/Guatemala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Sin MEDIA_URL público a propósito (sección 14.2 del prompt maestro:
# nada sensible se sirve desde una carpeta pública). Los archivos
# subidos (por ejemplo, el documento de respaldo de una justificación)
# se descargan por una vista autenticada que lee el archivo del disco,
# nunca por una URL servida directo desde MEDIA_ROOT.
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- DRF ----------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Deniega por defecto (sección 14.2): cada vista concede explícitamente.
    "DEFAULT_PERMISSION_CLASSES": ("apps.core.permissions.DenyAll",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",
        "user": "120/min",
        "login": "10/min",
        "verificacion_qr": "30/min",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "El Patojismo CDO — API",
    "DESCRIPTION": "Sistema de gestión académica del edificio CDO.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    # No fijado explícitamente por el prompt maestro (solo fija los 15
    # minutos del token de acceso) — 7 días es un valor de partida razonable
    # para no obligar a la familia a iniciar sesión todos los días;
    # TODO(confirmar): validar con dirección si el plazo debe ser distinto.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---- Frontend (para construir el enlace que codifica el QR de RF-14) -----

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

# ---- CORS -----------------------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# ---- Cookie del token de refresco (sección 14.1) --------------------------

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_SECURE = True
REFRESH_COOKIE_SAMESITE = "Strict"

# ---- Contraseñas comunes en español ---------------------------------------

COMMON_PASSWORDS_ES_FILE = BASE_DIR / "apps" / "core" / "data" / "contrasenas_comunes_es.txt"

# ---- Cabeceras de seguridad (sección 14.4, ADR-0007) -----------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"


def database_from_url(url: str) -> dict:
    """Arma el dict de DATABASES a partir de una DATABASE_URL, sin agregar
    una dependencia nueva (regla de trabajo 8) — psycopg ya está en
    requirements/base.txt para Postgres/Neon."""
    parsed = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username,
        "PASSWORD": parsed.password,
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
        "OPTIONS": {"sslmode": "require"},
        "CONN_MAX_AGE": 60,
    }
