import pytest

from apps.students.domain.internal_code import CapacidadCodigoInternoAgotada, generar_codigo_interno


def test_rn14_primer_codigo():
    assert generar_codigo_interno(1) == "ES001"


def test_rn14_codigo_alcanza_para_144_estudiantes_actuales():
    assert generar_codigo_interno(144) == "ES144"


def test_rn14_codigo_maximo():
    assert generar_codigo_interno(999) == "ES999"


def test_rn14_no_hay_codigo_cero():
    with pytest.raises(CapacidadCodigoInternoAgotada):
        generar_codigo_interno(0)


def test_rn14_no_hay_codigo_mas_alla_de_999():
    with pytest.raises(CapacidadCodigoInternoAgotada):
        generar_codigo_interno(1000)
