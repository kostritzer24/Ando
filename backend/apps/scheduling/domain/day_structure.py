"""RN-13: la jornada tiene seis períodos de 40 minutos y un receso de la
misma duración (entre el período 3 y el 4: 10:00–10:40). Los talleres son
de la tarde (14:00 a 19:00) y tienen su propia franja: cinco períodos de
una hora (7 a 11) que no se mezclan con los de la jornada matutina."""

from datetime import time

CANTIDAD_PERIODOS = 6
DURACION_MINUTOS = 40
PERIODOS_TALLER = (7, 8, 9, 10, 11)

HORARIO_PERIODOS: dict[int, tuple[time, time]] = {
    1: (time(8, 0), time(8, 40)),
    2: (time(8, 40), time(9, 20)),
    3: (time(9, 20), time(10, 0)),
    # 10:00–10:40 es el receso, no un período.
    4: (time(10, 40), time(11, 20)),
    5: (time(11, 20), time(12, 0)),
    6: (time(12, 0), time(12, 40)),
    # Franja de la tarde, solo para talleres.
    7: (time(14, 0), time(15, 0)),
    8: (time(15, 0), time(16, 0)),
    9: (time(16, 0), time(17, 0)),
    10: (time(17, 0), time(18, 0)),
    11: (time(18, 0), time(19, 0)),
}


class PeriodoInvalido(Exception):
    pass


def horario_de_periodo(numero: int) -> tuple[time, time]:
    if numero not in HORARIO_PERIODOS:
        raise PeriodoInvalido(f"El período debe estar entre 1 y {CANTIDAD_PERIODOS}.")
    return HORARIO_PERIODOS[numero]


def validar_periodo_para_seccion(numero: int, es_taller: bool) -> None:
    """Los cursos de la jornada usan los períodos 1 a 6; los talleres, los
    7 a 11 (la tarde, de 14:00 a 19:00)."""
    horario_de_periodo(numero)
    if es_taller and numero not in PERIODOS_TALLER:
        raise PeriodoInvalido("Los talleres son de la tarde: usa los períodos 7 a 11.")
    if not es_taller and numero in PERIODOS_TALLER:
        raise PeriodoInvalido("Los períodos 7 a 11 son solo para talleres.")
