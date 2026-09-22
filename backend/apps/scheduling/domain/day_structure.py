"""RN-13: la jornada tiene seis períodos de 40 minutos y un receso de la
misma duración (entre el período 3 y el 4: 10:00–10:40)."""

from datetime import time

CANTIDAD_PERIODOS = 6
DURACION_MINUTOS = 40

HORARIO_PERIODOS: dict[int, tuple[time, time]] = {
    1: (time(8, 0), time(8, 40)),
    2: (time(8, 40), time(9, 20)),
    3: (time(9, 20), time(10, 0)),
    # 10:00–10:40 es el receso, no un período.
    4: (time(10, 40), time(11, 20)),
    5: (time(11, 20), time(12, 0)),
    6: (time(12, 0), time(12, 40)),
}


class PeriodoInvalido(Exception):
    pass


def horario_de_periodo(numero: int) -> tuple[time, time]:
    if numero not in HORARIO_PERIODOS:
        raise PeriodoInvalido(f"El período debe estar entre 1 y {CANTIDAD_PERIODOS}.")
    return HORARIO_PERIODOS[numero]
