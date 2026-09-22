from decimal import Decimal

import pytest

from apps.grading.domain.template import CeldaPlantillaInvalida, validar_codigo, validar_punteo

_CODIGOS = {"ES001", "ES002"}


def test_codigo_valido_no_lanza_error():
    validar_codigo(numero_fila=2, internal_code="ES001", codigos_esperados=_CODIGOS)


def test_codigo_ajeno_es_invalido():
    with pytest.raises(CeldaPlantillaInvalida):
        validar_codigo(numero_fila=3, internal_code="ES999", codigos_esperados=_CODIGOS)


def test_punteo_valido_se_convierte_a_decimal():
    assert validar_punteo(
        numero_fila=2, nombre_actividad="Prueba corta", valor="8.5", max_score=Decimal("10")
    ) == Decimal("8.5")


def test_punteo_que_no_es_numero_es_invalido():
    with pytest.raises(CeldaPlantillaInvalida):
        validar_punteo(
            numero_fila=2, nombre_actividad="Prueba corta", valor="ocho", max_score=Decimal("10")
        )


def test_punteo_mayor_al_maximo_es_invalido():
    with pytest.raises(CeldaPlantillaInvalida):
        validar_punteo(
            numero_fila=2, nombre_actividad="Prueba corta", valor="15", max_score=Decimal("10")
        )


def test_punteo_negativo_es_invalido():
    with pytest.raises(CeldaPlantillaInvalida):
        validar_punteo(
            numero_fila=2, nombre_actividad="Prueba corta", valor="-1", max_score=Decimal("10")
        )
