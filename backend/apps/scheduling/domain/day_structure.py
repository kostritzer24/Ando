"""RN-13: la jornada tiene seis períodos de 40 minutos y un receso de la
misma duración, de 8:00 a 12:40. La institución maneja dos horarios que
solo se distinguen por dónde cae el receso:

- Básicos (primero y segundo): receso 10:00–10:40, después del período 3.
- Bachillerato (tercero básico, cuarto y quinto): receso 10:40–11:20,
  después del período 4. Tercero básico comparte el horario de
  bachillerato (horario real del ciclo 2026, oct. 2026).

Los talleres son de la tarde (14:00 a 19:00) y tienen su propia franja:
cinco períodos de una hora (7 a 11) que no se mezclan con los de la
jornada matutina."""

from datetime import time

CANTIDAD_PERIODOS = 6
DURACION_MINUTOS = 40
PERIODOS_TALLER = (7, 8, 9, 10, 11)

JORNADA_BASICOS = "basicos"
JORNADA_BACHILLERATO = "bachillerato"
JORNADAS = (JORNADA_BASICOS, JORNADA_BACHILLERATO)

_TARDE: dict[int, tuple[time, time]] = {
    7: (time(14, 0), time(15, 0)),
    8: (time(15, 0), time(16, 0)),
    9: (time(16, 0), time(17, 0)),
    10: (time(17, 0), time(18, 0)),
    11: (time(18, 0), time(19, 0)),
}

HORARIO_POR_JORNADA: dict[str, dict[int, tuple[time, time]]] = {
    JORNADA_BASICOS: {
        1: (time(8, 0), time(8, 40)),
        2: (time(8, 40), time(9, 20)),
        3: (time(9, 20), time(10, 0)),
        # 10:00–10:40 es el receso, no un período.
        4: (time(10, 40), time(11, 20)),
        5: (time(11, 20), time(12, 0)),
        6: (time(12, 0), time(12, 40)),
        **_TARDE,
    },
    JORNADA_BACHILLERATO: {
        1: (time(8, 0), time(8, 40)),
        2: (time(8, 40), time(9, 20)),
        3: (time(9, 20), time(10, 0)),
        4: (time(10, 0), time(10, 40)),
        # 10:40–11:20 es el receso, no un período.
        5: (time(11, 20), time(12, 0)),
        6: (time(12, 0), time(12, 40)),
        **_TARDE,
    },
}

# El período después del cual cae el receso, y su horario.
RECESO_POR_JORNADA: dict[str, tuple[int, time, time]] = {
    JORNADA_BASICOS: (3, time(10, 0), time(10, 40)),
    JORNADA_BACHILLERATO: (4, time(10, 40), time(11, 20)),
}

# Compatibilidad: el horario de básicos es el de referencia.
HORARIO_PERIODOS = HORARIO_POR_JORNADA[JORNADA_BASICOS]


class PeriodoInvalido(Exception):
    pass


def jornada_de_grado(grado: str) -> str:
    """Tercero básico, cuarto y quinto bachillerato siguen el horario de
    bachillerato; el resto (primero y segundo básico y los talleres) el de
    básicos."""
    grado = (grado or "").lower()
    return JORNADA_BACHILLERATO if "bachiller" in grado or "tercero" in grado else JORNADA_BASICOS


def horario_de_periodo(numero: int, jornada: str = JORNADA_BASICOS) -> tuple[time, time]:
    horario = HORARIO_POR_JORNADA[jornada]
    if numero not in horario:
        raise PeriodoInvalido(f"El período debe estar entre 1 y {CANTIDAD_PERIODOS}.")
    return horario[numero]


def periodos_se_cruzan(numero_a: int, jornada_a: str, numero_b: int, jornada_b: str) -> bool:
    """Dos clases chocan si sus horas reales se traslapan, no si comparten
    número de período: el 4 de bachillerato (10:00–10:40) y el 4 de básicos
    (10:40–11:20) no chocan, pero el 3 de básicos (9:20–10:00) y el 3 de
    bachillerato sí."""
    inicio_a, fin_a = horario_de_periodo(numero_a, jornada_a)
    inicio_b, fin_b = horario_de_periodo(numero_b, jornada_b)
    return inicio_a < fin_b and inicio_b < fin_a


def validar_periodo_para_seccion(numero: int, es_taller: bool) -> None:
    """Los cursos de la jornada usan los períodos 1 a 6; los talleres, los
    7 a 11 (la tarde, de 14:00 a 19:00)."""
    horario_de_periodo(numero)
    if es_taller and numero not in PERIODOS_TALLER:
        raise PeriodoInvalido("Los talleres son de la tarde: usa los períodos 7 a 11.")
    if not es_taller and numero in PERIODOS_TALLER:
        raise PeriodoInvalido("Los períodos 7 a 11 son solo para talleres.")
