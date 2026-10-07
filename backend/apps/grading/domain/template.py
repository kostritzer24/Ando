"""RF-19/RF-20: validación de cada celda de la plantilla de
calificaciones, antes de guardar nada (sección 14.4: vista previa con
los errores por fila, no un volcado técnico)."""

from decimal import Decimal, InvalidOperation


class CeldaPlantillaInvalida(Exception):
    def __init__(self, fila: int, mensaje: str):
        self.fila = fila
        self.mensaje = mensaje
        super().__init__(f"Fila {fila}: {mensaje}")


class PlantillaNoCorresponde(Exception):
    """La plantilla no es la que se descargó para esta asignación y unidad,
    o las actividades cambiaron desde entonces. Las columnas se leen por
    posición, así que cualquiera de los dos casos guardaría punteos en la
    actividad equivocada sin que nadie lo note."""


def validar_identidad(
    *,
    asignacion_esperada: str,
    unidad_esperada: str,
    actividades_esperadas: list[str],
    asignacion_recibida: str | None,
    unidad_recibida: str | None,
    actividades_recibidas: list[str],
) -> None:
    if asignacion_recibida is None:
        raise PlantillaNoCorresponde(
            "Este archivo no es una plantilla descargada del sistema. "
            "Descargá la plantilla de nuevo y cargá esa."
        )
    if asignacion_recibida != asignacion_esperada or unidad_recibida != unidad_esperada:
        raise PlantillaNoCorresponde(
            "Esta plantilla es de otro curso o de otra unidad. "
            "Revisá que elegiste el curso y la unidad correctos."
        )
    if actividades_recibidas != actividades_esperadas:
        raise PlantillaNoCorresponde(
            "Las actividades de la unidad cambiaron desde que descargaste esta plantilla. "
            "Descargala de nuevo y pasá los punteos a la nueva."
        )


def validar_encabezados(*, esperados: list[str], recibidos: list) -> None:
    """Detecta columnas movidas, borradas o agregadas a mano."""
    recibidos_texto = [str(valor).strip() if valor is not None else "" for valor in recibidos]
    if recibidos_texto[: len(esperados)] != esperados or any(recibidos_texto[len(esperados) :]):
        raise PlantillaNoCorresponde(
            "Las columnas de la plantilla se movieron o se cambiaron. "
            "No cambies el orden ni los títulos; descargala de nuevo si hace falta."
        )


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
