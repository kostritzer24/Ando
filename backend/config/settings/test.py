from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "clave-de-pruebas-suficientemente-larga-para-jwt-y-firma-de-sesion"
ALLOWED_HOSTS = ["testserver", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

REFRESH_COOKIE_SECURE = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # más rápido para pruebas
]
