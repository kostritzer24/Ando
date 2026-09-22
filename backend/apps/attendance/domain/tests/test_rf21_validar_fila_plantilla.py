import pytest

from apps.attendance.domain.template import FilaPlantillaInvalida, validar_fila

_CODIGOS = {"ES001", "ES002"}


def test_fila_valida_no_lanza_error():
    validar_fila(
        numero_fila=2, internal_code="ES001", status="presente", codigos_esperados=_CODIGOS
    )


def test_codigo_fuera_de_la_seccion_es_invalido():
    with pytest.raises(FilaPlantillaInvalida):
        validar_fila(
            numero_fila=3, internal_code="ES999", status="presente", codigos_esperados=_CODIGOS
        )


def test_codigo_vacio_es_invalido():
    with pytest.raises(FilaPlantillaInvalida):
        validar_fila(numero_fila=4, internal_code="", status="presente", codigos_esperados=_CODIGOS)


def test_estado_invalido_es_rechazado():
    with pytest.raises(FilaPlantillaInvalida):
        validar_fila(
            numero_fila=5, internal_code="ES001", status="de-vacaciones", codigos_esperados=_CODIGOS
        )


def test_el_mensaje_de_error_incluye_el_numero_de_fila():
    with pytest.raises(FilaPlantillaInvalida) as excinfo:
        validar_fila(
            numero_fila=7, internal_code="ES999", status="presente", codigos_esperados=_CODIGOS
        )
    assert "Fila 7" in str(excinfo.value)
