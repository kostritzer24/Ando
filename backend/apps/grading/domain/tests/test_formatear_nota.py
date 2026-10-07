from decimal import Decimal

from apps.grading.domain.report_card import formatear_nota


def test_formatear_nota_quita_los_ceros_de_relleno():
    assert formatear_nota(Decimal("85.00")) == "85"
    assert formatear_nota(Decimal("85.50")) == "85.5"
    assert formatear_nota(Decimal("0")) == "0"
