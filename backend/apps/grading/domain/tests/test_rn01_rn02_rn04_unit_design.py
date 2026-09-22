from decimal import Decimal

import pytest

from apps.grading.domain.unit_design import (
    DefinicionDeUnidadInvalida,
    validar_nuevo_punteo_maximo,
    validar_unidad_completa,
)


def test_rn02_una_actividad_dentro_del_tope_es_valida():
    validar_nuevo_punteo_maximo(Decimal("60"), Decimal("40"))


def test_rn02_pasarse_de_cien_puntos_es_invalido():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_nuevo_punteo_maximo(Decimal("70"), Decimal("40"))


def test_rn02_llegar_exactamente_a_cien_es_valido():
    validar_nuevo_punteo_maximo(Decimal("0"), Decimal("100"))


def test_actividad_con_punteo_cero_es_invalida():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_nuevo_punteo_maximo(Decimal("0"), Decimal("0"))


def test_rn01_rn04_unidad_completa_con_cuatro_pruebas_cortas_y_cien_puntos():
    validar_unidad_completa(suma_max_score=Decimal("100"), cantidad_pruebas_cortas=4)


def test_rn04_mas_de_cuatro_pruebas_cortas_tambien_es_valido():
    validar_unidad_completa(suma_max_score=Decimal("100"), cantidad_pruebas_cortas=6)


def test_rn04_menos_de_cuatro_pruebas_cortas_es_invalido():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_unidad_completa(suma_max_score=Decimal("100"), cantidad_pruebas_cortas=3)


def test_rn02_unidad_incompleta_es_invalida():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_unidad_completa(suma_max_score=Decimal("80"), cantidad_pruebas_cortas=4)
