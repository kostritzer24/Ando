"""RF-23 / RF-10 / RN-05: reglas de una solicitud de modificación de nota.
Las cadenas de estado las pasa quien llama (`grading/services/
grade_change_request.py`), igual que en `report_card.py`, para que el
dominio no dependa de Django."""

from datetime import date
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
            "Espera a que Dirección la resuelva."
        )


def validar_resolucion(*, estado_actual: str, estado_pendiente: str) -> None:
    if estado_actual != estado_pendiente:
        raise SolicitudDeModificacionInvalida("Esta solicitud ya fue resuelta.")


def puede_corregirse_sin_autorizacion(*, hoy: date, fecha_entrega_notas: date) -> bool:
    """RN-05 aplicada a notas ya entregadas: hasta la fecha de entrega de
    notas de la unidad (RN-10) el docente corrige su propio error de dedo
    directamente, con bitácora; desde el día siguiente las notas son
    oficiales y cualquier cambio pasa por la autorización de Dirección.
    Mismo corte que RN-07 para la plantilla recargada. Sin este plazo, un
    error de dedo al capturar quedaba fijo hasta que Dirección aprobara
    una solicitud (sección 15.2: "guardar las notas de toda una sección sin
    poder corregir un error de dedo es inaceptable")."""
    return hoy <= fecha_entrega_notas


def validar_correccion_directa(
    *,
    punteo_nuevo: Decimal,
    nota_vigente: Decimal,
    max_score: Decimal,
    hoy: date,
    fecha_entrega_notas: date,
    hay_pendiente: bool,
) -> None:
    if not puede_corregirse_sin_autorizacion(hoy=hoy, fecha_entrega_notas=fecha_entrega_notas):
        raise SolicitudDeModificacionInvalida(
            f"La entrega de notas de esta unidad cerró el {fecha_entrega_notas:%d/%m/%Y}. "
            "Para cambiar esta nota, solicita una corrección a Dirección."
        )
    if hay_pendiente:
        raise SolicitudDeModificacionInvalida(
            "Esta nota tiene una solicitud de corrección pendiente; espera a que Dirección "
            "la resuelva."
        )
    if not (Decimal("0") <= punteo_nuevo <= max_score):
        raise SolicitudDeModificacionInvalida(f"El punteo debe estar entre 0 y {max_score}.")
    if punteo_nuevo == nota_vigente:
        raise SolicitudDeModificacionInvalida("Ese punteo es igual a la nota que ya tiene.")
