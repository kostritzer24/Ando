"""RN-13: la jornada tiene seis períodos de 40 minutos y un receso de la
misma duración (entre el período 3 y el 4: 10:00–10:40). Los talleres son
de la tarde y tienen su propia franja: tres períodos de 40 minutos
(7 a 9) que no se mezclan con los de la jornada matutina."""

from datetime import time

CANTIDAD_PERIODOS = 6
DURACION_MINUTOS = 40
PERIODOS_TALLER = (7, 8, 9)

HORARIO_PERIODOS: dict[int, tuple[time, time]] = {
    1: (time(8, 0), time(8, 40)),
    2: (time(8, 40), time(9, 20)),
    3: (time(9, 20), time(10, 0)),
    # 10:00–10:40 es el receso, no un período.
    4: (time(10, 40), time(11, 20)),
    5: (time(11, 20), time(12, 0)),
    6: (time(12, 0), time(12, 40)),
    # Franja de la tarde, solo para talleres.
    7: (time(13, 30), time(14, 10)),
    8: (time(14, 10), time(14, 50)),
    9: (time(14, 50), time(15, 30)),
}


class PeriodoInvalido(Exception):
    pass


def horario_de_periodo(numero: int) -> tuple[time, time]:
    if numero not in HORARIO_PERIODOS:
        raise PeriodoInvalido(f"El período debe estar entre 1 y {CANTIDAD_PERIODOS}.")
    return HORARIO_PERIODOS[numero]


def validar_periodo_para_seccion(numero: int, es_taller: bool) -> None:
    """Los cursos de la jornada usan los períodos 1 a 6; los talleres, los
    7 a 9 (la tarde)."""
    horario_de_periodo(numero)
    if es_taller and numero not in PERIODOS_TALLER:
        raise PeriodoInvalido("Los talleres son de la tarde: usa los períodos 7 a 9.")
    if not es_taller and numero in PERIODOS_TALLER:
        raise PeriodoInvalido("Los períodos 7 a 9 son solo para talleres.")
