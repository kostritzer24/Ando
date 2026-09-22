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

# El límite de tasa (sección 14.4) usa una caché en memoria que vive todo
# el proceso de pytest, no por prueba — con cientos de pruebas haciendo
# varias peticiones cada una, el contador termina superando el límite y
# empieza a devolver 429 en pruebas que no tienen nada que ver con el
# límite de tasa en sí. Se sube muchísimo acá (no se quita del todo: las
# vistas que fijan su propio `throttle_scope`, como el login, necesitan
# que la clave exista en DEFAULT_THROTTLE_RATES o truenan con
# ImproperlyConfigured). El límite de tasa real se prueba aparte, con su
# propia caché controlada, no como efecto colateral de la suite
# funcional completa.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000000/min",
        "user": "1000000/min",
        "login": "1000000/min",
        "verificacion_qr": "1000000/min",
    },
}
