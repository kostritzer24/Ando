"""Quinto bachillerato solo cursa 3 unidades (indicado por el centro, oct. 2026)."""

from decimal import Decimal

import pytest

from apps.grading.domain.report_card import (
    armar_fila_cuadro,
    promedio_de_unidades,
    unidades_del_grado,
)


@pytest.mark.parametrize(
    ("grado", "unidades"),
    [
        ("Primero básico", 4),
        ("Tercero básico", 4),
        ("Cuarto bachillerato", 4),
        ("Quinto bachillerato", 3),
        ("quinto Bachillerato", 3),
    ],
)
def test_unidades_del_grado(grado, unidades):
    assert unidades_del_grado(grado) == unidades


def test_quinto_arma_el_cuadro_con_tres_unidades():
    fila = armar_fila_cuadro({1: Decimal("80"), 2: Decimal("70"), 3: Decimal("90")}, 3)
    assert fila["unidades"] == [Decimal("80"), Decimal("70"), Decimal("90")]
    assert fila["promedio"] == 80
    assert promedio_de_unidades([fila]) == [80, 70, 90, 80]
