from datetime import time

import pytest

from apps.scheduling.domain.day_structure import (
    CANTIDAD_PERIODOS,
    DURACION_MINUTOS,
    PeriodoInvalido,
    horario_de_periodo,
)


def test_rn13_hay_seis_periodos():
    assert CANTIDAD_PERIODOS == 6


def test_rn13_cada_periodo_dura_cuarenta_minutos():
    for numero in range(1, CANTIDAD_PERIODOS + 1):
        inicio, fin = horario_de_periodo(numero)
        minutos = (fin.hour * 60 + fin.minute) - (inicio.hour * 60 + inicio.minute)
        assert minutos == DURACION_MINUTOS


def test_rn13_primer_periodo_empieza_a_las_ocho():
    inicio, _fin = horario_de_periodo(1)
    assert inicio == time(8, 0)


def test_rn13_hay_un_receso_de_cuarenta_minutos_entre_el_tercer_y_cuarto_periodo():
    _inicio, fin_tercero = horario_de_periodo(3)
    inicio_cuarto, _fin = horario_de_periodo(4)
    minutos_receso = (inicio_cuarto.hour * 60 + inicio_cuarto.minute) - (
        fin_tercero.hour * 60 + fin_tercero.minute
    )
    assert minutos_receso == DURACION_MINUTOS


@pytest.mark.parametrize("numero", [0, 7, -1])
def test_rn13_periodo_fuera_de_rango_es_invalido(numero):
    with pytest.raises(PeriodoInvalido):
        horario_de_periodo(numero)
