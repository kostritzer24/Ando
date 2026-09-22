from decimal import Decimal

import pytest

from apps.grading.domain.scoring import (
    NOTA_MINIMA_APROBACION,
    aprueba_curso,
    calcular_nota_final,
    calcular_nota_unidad,
)


def test_nota_de_unidad_es_la_suma_de_los_punteos():
    assert calcular_nota_unidad(
        [Decimal("10"), Decimal("10"), Decimal("10"), Decimal("10"), Decimal("60")]
    ) == Decimal("100")


def test_nota_de_unidad_sin_calificaciones_es_cero():
    assert calcular_nota_unidad([]) == Decimal("0")


def test_rn02_nota_final_es_el_promedio_de_las_cuatro_unidades():
    assert calcular_nota_final([Decimal("80"), Decimal("80"), Decimal("80"), Decimal("80")]) == 80


@pytest.mark.parametrize(
    "notas,esperado",
    [
        ([Decimal("79"), Decimal("80"), Decimal("80"), Decimal("80")], 80),  # promedio 79.75
        (
            [Decimal("79"), Decimal("79"), Decimal("80"), Decimal("80")],
            80,
        ),  # promedio 79.5 -> arriba
        ([Decimal("78"), Decimal("79"), Decimal("80"), Decimal("80")], 79),  # promedio 79.25
    ],
)
def test_adr0003_redondeo_aritmetico_estandar_mitad_hacia_arriba(notas, esperado):
    assert calcular_nota_final(notas) == esperado


def test_calcular_nota_final_sin_notas_lanza_error():
    with pytest.raises(ValueError):
        calcular_nota_final([])


def test_rn03_sesenta_puntos_aprueba():
    assert aprueba_curso(NOTA_MINIMA_APROBACION) is True


def test_rn03_cincuenta_y_nueve_puntos_no_aprueba():
    assert aprueba_curso(59) is False


def test_rn03_nota_perfecta_aprueba():
    assert aprueba_curso(100) is True
