"""RN-01 (escala 1-100), RN-02 (el total de la unidad no pasa de 100) y
RN-04 revisada por ADR-0003 (mínimo 4 pruebas cortas, sin exigir que
sean exactamente 4 ni que valgan 10 puntos cada una)."""

from decimal import Decimal

MAXIMO_PUNTOS_POR_UNIDAD = Decimal("100")
MINIMO_PRUEBAS_CORTAS = 4


class DefinicionDeUnidadInvalida(Exception):
    pass


def validar_nuevo_punteo_maximo(suma_actual: Decimal, nuevo_max_score: Decimal) -> None:
    """Se valida en cada Actividad que se crea: la suma nunca puede
    superar los 100 puntos, aunque la unidad todavía no esté completa."""
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
