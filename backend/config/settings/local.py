import os

from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "clave-de-desarrollo-no-usar-en-produccion")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    DATABASES = {"default": database_from_url(_database_url)}  # noqa: F405
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }

CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS or ["http://localhost:5173"]  # noqa: F405

# En local no hace falta HTTPS para probar en la máquina propia.
REFRESH_COOKIE_SECURE = False
