from decimal import Decimal

from apps.grading.domain.report_card import armar_filas_del_boletin, formatear_nota


def test_formatear_nota_quita_los_ceros_de_relleno():
    assert formatear_nota(Decimal("85.00")) == "85"
    assert formatear_nota(Decimal("85.50")) == "85.5"
    assert formatear_nota(Decimal("0")) == "0"


def test_rn03_antes_de_la_ultima_unidad_no_hay_nota_final_ni_reprobado():
    filas = armar_filas_del_boletin(
        cursos=[("Matemática", [Decimal("40"), Decimal("55")])], unidad_actual=2
    )

    assert filas == [{"nombre": "Matemática", "notas": ["40", "55"]}]


def test_rn02_rn03_en_la_ultima_unidad_hay_nota_final_redondeada_y_resultado():
    filas = armar_filas_del_boletin(
        cursos=[
            ("Matemática", [Decimal("59"), Decimal("60"), Decimal("60"), Decimal("59")]),
            ("Lenguaje", [Decimal("50"), Decimal("50"), Decimal("50"), Decimal("50")]),
        ],
        unidad_actual=4,
    )

    assert filas[0]["final"] == 60 and filas[0]["aprobado"] is True  # 59.5 → 60
    assert filas[1]["final"] == 50 and filas[1]["aprobado"] is False
