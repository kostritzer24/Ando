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


@pytest.mark.parametrize("numero", [0, 12, -1])
def test_rn13_periodo_fuera_de_rango_es_invalido(numero):
    with pytest.raises(PeriodoInvalido):
        horario_de_periodo(numero)


def test_rn13_bachillerato_tiene_el_receso_entre_el_cuarto_y_el_quinto_periodo():
    from apps.scheduling.domain.day_structure import JORNADA_BACHILLERATO

    _inicio, fin_cuarto = horario_de_periodo(4, JORNADA_BACHILLERATO)
    inicio_quinto, _fin = horario_de_periodo(5, JORNADA_BACHILLERATO)
    assert (fin_cuarto, inicio_quinto) == (time(10, 40), time(11, 20))


def test_rn13_los_dos_horarios_cubren_la_misma_jornada_de_8_a_12_40():
    from apps.scheduling.domain.day_structure import JORNADAS

    for jornada in JORNADAS:
        assert horario_de_periodo(1, jornada)[0] == time(8, 0)
        assert horario_de_periodo(6, jornada)[1] == time(12, 40)


@pytest.mark.parametrize(
    ("grado", "jornada"),
    [
        ("Primero básico", "basicos"),
        ("Segundo básico", "basicos"),
        ("Tercero básico", "bachillerato"),
        ("Cuarto bachillerato", "bachillerato"),
        ("Quinto Bachillerato", "bachillerato"),
        ("Taller de panadería", "basicos"),
    ],
)
def test_rn13_la_jornada_sale_del_grado(grado, jornada):
    from apps.scheduling.domain.day_structure import jornada_de_grado

    assert jornada_de_grado(grado) == jornada


def test_rn13_el_cruce_se_mide_por_hora_real_no_por_numero_de_periodo():
    from apps.scheduling.domain.day_structure import periodos_se_cruzan

    # P4 de bachillerato (10:00–10:40) y P4 de básicos (10:40–11:20): no chocan.
    assert not periodos_se_cruzan(4, "bachillerato", 4, "basicos")
    # P3 es igual en los dos horarios: sí chocan.
    assert periodos_se_cruzan(3, "bachillerato", 3, "basicos")
