from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ValidationError


@lru_cache(maxsize=1)
def _lista_contrasenas_comunes() -> frozenset[str]:
    try:
        contenido = settings.COMMON_PASSWORDS_ES_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return frozenset()
    return frozenset(linea.strip().lower() for linea in contenido.splitlines() if linea.strip())


class ContrasenaComunEsValidator:
    """Rechaza contraseñas de la lista de contraseñas comunes en español
    (sección 14.1: "más una lista de contraseñas comunes en español"),
    además de la lista en inglés que ya trae Django."""

    def validate(self, password: str, user=None) -> None:
        if password.lower() in _lista_contrasenas_comunes():
            raise ValidationError(
                "Esta contraseña es muy común. Elegí una distinta.",
                code="password_too_common_es",
            )

    def get_help_text(self) -> str:
        return "La contraseña no puede ser una de uso muy común en español."
