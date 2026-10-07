import pytest

from apps.grading.domain.template import (
    PlantillaNoCorresponde,
    validar_encabezados,
    validar_identidad,
)

ESPERADA = {"asignacion_esperada": "a", "unidad_esperada": "u", "actividades_esperadas": ["x", "y"]}


def test_hu20_la_plantilla_correcta_pasa():
    validar_identidad(
        **ESPERADA,
        asignacion_recibida="a",
        unidad_recibida="u",
        actividades_recibidas=["x", "y"],
    )


@pytest.mark.parametrize(
    "recibida",
    [
        {"asignacion_recibida": None, "unidad_recibida": None, "actividades_recibidas": []},
        {"asignacion_recibida": "b", "unidad_recibida": "u", "actividades_recibidas": ["x", "y"]},
        {"asignacion_recibida": "a", "unidad_recibida": "v", "actividades_recibidas": ["x", "y"]},
        {"asignacion_recibida": "a", "unidad_recibida": "u", "actividades_recibidas": ["y", "x"]},
        {"asignacion_recibida": "a", "unidad_recibida": "u", "actividades_recibidas": ["x"]},
    ],
)
def test_hu20_plantilla_ajena_o_desactualizada_es_rechazada(recibida):
    with pytest.raises(PlantillaNoCorresponde):
        validar_identidad(**ESPERADA, **recibida)


def test_hu20_encabezados_iguales_pasan_aunque_sobren_celdas_vacias():
    validar_encabezados(
        esperados=["Código", "Nombre", "A"], recibidos=["Código", "Nombre", "A", None]
    )


@pytest.mark.parametrize(
    "recibidos",
    [["Código", "A", "Nombre"], ["Código", "Nombre"], ["Código", "Nombre", "A", "Extra"]],
)
def test_hu20_columnas_movidas_borradas_o_agregadas_son_rechazadas(recibidos):
    with pytest.raises(PlantillaNoCorresponde):
        validar_encabezados(esperados=["Código", "Nombre", "A"], recibidos=recibidos)
