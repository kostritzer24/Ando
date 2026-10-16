import os

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = [h.strip() for h in os.environ["ALLOWED_HOSTS"].split(",") if h.strip()]

DATABASES = {"default": database_from_url(os.environ["DATABASE_URL"])}  # noqa: F405

MIDDLEWARE = [  # noqa: F405
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Detrás del proxy de Render el servidor ve HTTP; el proxy avisa por esta
# cabecera que la petición original fue HTTPS (sin ella, el redireccionamiento
# a HTTPS entraría en bucle).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTPS y cookies seguras (sección 14.4). La comprobación de salud de la
# plataforma llega por la red interna y no se redirige.
SECURE_REDIRECT_EXEMPT = [r"^healthz/?$"]
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
