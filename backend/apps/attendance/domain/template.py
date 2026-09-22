"""RF-21: validación de cada fila de la plantilla de asistencia de
talleres, antes de guardar nada (sección 14.4 del prompt maestro: vista
previa con los errores por fila)."""

from ..models import Attendance

_ESTADOS_VALIDOS = {codigo for codigo, _ in Attendance.ESTADOS}


class FilaPlantillaInvalida(Exception):
    def __init__(self, fila: int, mensaje: str):
        self.fila = fila
        self.mensaje = mensaje
        super().__init__(f"Fila {fila}: {mensaje}")


def validar_fila(
    *, numero_fila: int, internal_code: str, status: str, codigos_esperados: set
) -> None:
    if not internal_code:
        raise FilaPlantillaInvalida(numero_fila, "Falta el código del estudiante.")
    if internal_code not in codigos_esperados:
        raise FilaPlantillaInvalida(
            numero_fila, f"El código '{internal_code}' no pertenece a esta sección."
        )
    if status not in _ESTADOS_VALIDOS:
        estados = ", ".join(sorted(_ESTADOS_VALIDOS))
        raise FilaPlantillaInvalida(
            numero_fila, f"El estado '{status}' no es válido. Debe ser uno de: {estados}."
        )
