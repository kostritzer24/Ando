"""RN-08: es solvente el estudiante que está al día con su mensualidad o
que cuenta con beca. "Al día" se entiende como tener un pago registrado
por cada mes del ciclo transcurrido hasta la fecha de referencia — no
solo el mes en curso, para que un mes salteado en el pasado siga
marcando al estudiante como insolvente."""

from datetime import date


def meses_del_periodo(*, inicio: date, hasta: date) -> set[tuple[int, int]]:
    """Meses (año, mes) que van de `inicio` a `hasta`, inclusive."""
    if hasta < inicio:
        return set()
    meses: set[tuple[int, int]] = set()
    anio, mes = inicio.year, inicio.month
    while (anio, mes) <= (hasta.year, hasta.month):
        meses.add((anio, mes))
        mes += 1
        if mes == 13:
            mes = 1
            anio += 1
    return meses


def es_solvente(
    *, tiene_beca: bool, meses_esperados: set[tuple[int, int]], meses_pagados: set[tuple[int, int]]
) -> bool:
    if tiene_beca:
        return True
    return meses_esperados <= meses_pagados
