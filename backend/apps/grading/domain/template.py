"""RF-19/RF-20: validación de cada celda de la plantilla de
calificaciones, antes de guardar nada (sección 14.4: vista previa con
los errores por fila, no un volcado técnico)."""

from decimal import Decimal, InvalidOperation


class CeldaPlantillaInvalida(Exception):
    def __init__(self, fila: int, mensaje: str):
        self.fila = fila
        self.mensaje = mensaje
        super().__init__(f"Fila {fila}: {mensaje}")


def validar_codigo(*, numero_fila: int, internal_code: str, codigos_esperados: set) -> None:
    if not internal_code:
        raise CeldaPlantillaInvalida(numero_fila, "Falta el código del estudiante.")
    if internal_code not in codigos_esperados:
        raise CeldaPlantillaInvalida(
            numero_fila, f"El código '{internal_code}' no pertenece a esta sección."
        )


def validar_punteo(
    *, numero_fila: int, nombre_actividad: str, valor, max_score: Decimal
) -> Decimal:
    try:
        punteo = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CeldaPlantillaInvalida(
            numero_fila, f"'{valor}' no es un número válido para '{nombre_actividad}'."
        ) from exc
    if not (Decimal("0") <= punteo <= max_score):
        raise CeldaPlantillaInvalida(
            numero_fila, f"El punteo de '{nombre_actividad}' debe estar entre 0 y {max_score}."
        )
    return punteo
