"""
RNF-05: "Límite de intentos de inicio de sesión por usuario y por
dirección IP, con bloqueo temporal creciente." Regla pura, sin Django.
"""

from datetime import timedelta

UMBRAL_BLOQUEO = 5

_ESCALADA: dict[int, timedelta] = {
    5: timedelta(minutes=1),
    6: timedelta(minutes=5),
    7: timedelta(minutes=15),
}
_ESCALADA_MAXIMA = timedelta(hours=1)


def calcular_bloqueo(intentos_fallidos: int) -> timedelta | None:
    """Devuelve cuánto debe durar el bloqueo dado el número de intentos
    fallidos acumulados, o None si todavía no corresponde bloquear."""
    if intentos_fallidos < UMBRAL_BLOQUEO:
        return None
    return _ESCALADA.get(intentos_fallidos, _ESCALADA_MAXIMA)
