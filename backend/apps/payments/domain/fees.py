"""Cuotas del centro: la mensualidad depende del ciclo de estudios
(básico o bachillerato) y la inscripción es una sola por ciclo escolar.
Los importes los fija el sistema, nunca se reciben del cliente."""

from decimal import Decimal

CUOTA_MENSUAL_BASICO = Decimal("100.00")
CUOTA_MENSUAL_BACHILLERATO = Decimal("150.00")
CUOTA_INSCRIPCION = Decimal("200.00")


class CuotaNoDeterminada(Exception):
    pass


def cuota_mensual(grado: str) -> Decimal:
    """Q100 en básico, Q150 en bachillerato. El grado se reconoce por su
    nombre («Segundo básico», «Quinto bachillerato»)."""
    normalizado = grado.lower().replace("á", "a")
    if "bachiller" in normalizado:
        return CUOTA_MENSUAL_BACHILLERATO
    if "basico" in normalizado:
        return CUOTA_MENSUAL_BASICO
    raise CuotaNoDeterminada(
        f"No se pudo determinar si «{grado}» es de básico o de bachillerato; "
        "revisa el nombre del grado en Datos maestros."
    )
