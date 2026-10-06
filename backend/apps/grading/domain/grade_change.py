"""RF-23 / RF-10 / RN-05: reglas de una solicitud de modificación de nota.
Las cadenas de estado las pasa quien llama (`grading/services/
grade_change_request.py`), igual que en `report_card.py`, para que el
dominio no dependa de Django."""

from decimal import Decimal


class SolicitudDeModificacionInvalida(Exception):
    pass


def validar_solicitud(
    *, punteo_propuesto: Decimal, nota_vigente: Decimal, max_score: Decimal, hay_pendiente: bool
) -> None:
    """Una sola solicitud pendiente por nota: con dos, aprobar ambas deja
    la nota en la que se resuelva última, y cada una se pidió contra una
    nota vigente que la otra ya cambió."""
    if not (Decimal("0") <= punteo_propuesto <= max_score):
        raise SolicitudDeModificacionInvalida(
            f"El punteo propuesto debe estar entre 0 y {max_score}."
        )
    if punteo_propuesto == nota_vigente:
        raise SolicitudDeModificacionInvalida(
            "El punteo propuesto es igual a la nota vigente; no hay nada que corregir."
        )
    if hay_pendiente:
        raise SolicitudDeModificacionInvalida(
            "Esta nota ya tiene una solicitud de corrección pendiente. "
            "Esperá a que Dirección la resuelva."
        )


def validar_resolucion(*, estado_actual: str, estado_pendiente: str) -> None:
    if estado_actual != estado_pendiente:
        raise SolicitudDeModificacionInvalida("Esta solicitud ya fue resuelta.")
