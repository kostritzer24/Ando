"""RN-01 (escala 1-100), RN-02 (el total de la unidad no pasa de 100) y
RN-04 revisada por ADR-0003 (mínimo 4 pruebas cortas, sin exigir que
sean exactamente 4 ni que valgan 10 puntos cada una). RN-20 a RN-22
(oct 2026): repartir puntos, actividad sin punteo máximo y unidad
promediada."""

from decimal import ROUND_DOWN, Decimal

MAXIMO_PUNTOS_POR_UNIDAD = Decimal("100")
MINIMO_PRUEBAS_CORTAS = 4


class DefinicionDeUnidadInvalida(Exception):
    pass


CENTAVO = Decimal("0.01")


def validar_nuevo_punteo_maximo(suma_actual: Decimal, nuevo_max_score: Decimal | None) -> None:
    """Se valida en cada Actividad que se crea: la suma nunca puede
    superar los 100 puntos, aunque la unidad todavía no esté completa. Una
    actividad sin punteo todavía (RF-39) no suma nada."""
    if nuevo_max_score is None:
        return
    if nuevo_max_score <= 0:
        raise DefinicionDeUnidadInvalida(
            "El punteo máximo de una actividad debe ser mayor que cero."
        )
    if suma_actual + nuevo_max_score > MAXIMO_PUNTOS_POR_UNIDAD:
        raise DefinicionDeUnidadInvalida(
            f"La unidad no puede superar los {MAXIMO_PUNTOS_POR_UNIDAD} puntos "
            f"(ya lleva {suma_actual}, esta actividad agregaría {nuevo_max_score})."
        )


def validar_unidad_completa(*, suma_max_score: Decimal, cantidad_pruebas_cortas: int) -> None:
    """Se valida antes de registrar punteo real o generar la plantilla de
    calificaciones (RF-18/RF-19): la unidad tiene que estar
    completamente diseñada primero."""
    if suma_max_score != MAXIMO_PUNTOS_POR_UNIDAD:
        raise DefinicionDeUnidadInvalida(
            f"La unidad debe sumar exactamente {MAXIMO_PUNTOS_POR_UNIDAD} puntos "
            f"(lleva {suma_max_score})."
        )
    if cantidad_pruebas_cortas < MINIMO_PRUEBAS_CORTAS:
        raise DefinicionDeUnidadInvalida(
            f"La unidad necesita al menos {MINIMO_PRUEBAS_CORTAS} pruebas cortas "
            f"(lleva {cantidad_pruebas_cortas})."
        )


def validar_cambio_de_punteo_maximo(*, tiene_notas: bool) -> None:
    """Con notas ya registradas, cambiar el máximo deja punteos que valen
    sobre otro total (un 9/10 pasaría a ser 9/5, o quedaría por encima del
    nuevo máximo)."""
    if tiene_notas:
        raise DefinicionDeUnidadInvalida(
            "Esta actividad ya tiene notas registradas; su punteo máximo ya no se puede cambiar."
        )


def validar_baja_de_actividad(*, tiene_notas: bool) -> None:
    """Una actividad calificada no se da de baja: sus notas dejarían de
    contar en la nota de unidad, y el espacio liberado en los 100 puntos
    permitiría agregar otra encima."""
    if tiene_notas:
        raise DefinicionDeUnidadInvalida(
            "Esta actividad ya tiene notas registradas; no se puede dar de baja."
        )


def repartir_puntos(fijos: list[Decimal], libres: int) -> list[Decimal]:
    """RN-20: lo que dejan libre las actividades ya calificadas (`fijos`,
    que conservan su punteo) se divide en partes iguales entre las
    `libres`, con dos decimales; la última se lleva el residuo para que
    la unidad sume exactamente 100."""
    if libres <= 0:
        raise DefinicionDeUnidadInvalida(
            "No hay actividades sin notas entre las cuales repartir los puntos."
        )
    restante = MAXIMO_PUNTOS_POR_UNIDAD - sum(fijos, Decimal("0"))
    parte = (restante / libres).quantize(CENTAVO, rounding=ROUND_DOWN)
    if parte <= 0:
        raise DefinicionDeUnidadInvalida(
            f"Las actividades ya calificadas suman {MAXIMO_PUNTOS_POR_UNIDAD - restante} puntos; "
            "no queda lo suficiente para repartir entre las demás."
        )
    partes = [parte] * libres
    partes[-1] = restante - parte * (libres - 1)
    return partes


def validar_actividad_calificable(*, max_score: Decimal | None, nombre: str) -> None:
    """RN-21: sin punteo máximo no hay contra qué validar el punteo."""
    if max_score is None:
        raise DefinicionDeUnidadInvalida(
            f"'{nombre}' todavía no tiene punteo máximo; asígnaselo o reparte los puntos "
            "antes de calificarla."
        )


def validar_cambio_de_promedio(*, hay_boletin_aprobado: bool) -> None:
    """RN-22: aprobar un boletín congela su contenido; cambiar el promedio
    después dejaría el boletín con otra nota que la del sistema."""
    if hay_boletin_aprobado:
        raise DefinicionDeUnidadInvalida(
            "Dirección ya aprobó boletines de esta unidad; el promedio ya no se puede cambiar."
        )


def validar_promedio(*, puntos_evaluados: Decimal) -> None:
    if puntos_evaluados <= 0:
        raise DefinicionDeUnidadInvalida(
            "Para promediar, la unidad necesita al menos una actividad con punteo máximo."
        )
