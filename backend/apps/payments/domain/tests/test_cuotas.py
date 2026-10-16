from decimal import Decimal

import pytest

from apps.payments.domain.fees import CuotaNoDeterminada, cuota_mensual


@pytest.mark.parametrize(
    "grado", ["Primero básico", "Segundo Básico", "tercero basico", "Cuarto básico"]
)
def test_la_mensualidad_de_basico_es_q100(grado):
    assert cuota_mensual(grado) == Decimal("100.00")


@pytest.mark.parametrize("grado", ["Cuarto bachillerato", "Quinto Bachillerato en ciencias"])
def test_la_mensualidad_de_bachillerato_es_q150(grado):
    assert cuota_mensual(grado) == Decimal("150.00")


def test_un_grado_que_no_es_ni_basico_ni_bachillerato_no_tiene_cuota():
    with pytest.raises(CuotaNoDeterminada):
        cuota_mensual("Parvulos")
