from datetime import date

from apps.catalog.domain.grading_unit import (
    calcular_fecha_entrega_notas,
    calcular_fecha_habilitacion_boletin,
)


def test_rn10_entrega_de_notas_quince_dias_despues_del_cierre():
    cierre = date(2026, 2, 28)
    assert calcular_fecha_entrega_notas(cierre) == date(2026, 3, 15)


def test_rn10_boletin_se_habilita_una_semana_despues_de_la_entrega():
    entrega = date(2026, 3, 15)
    assert calcular_fecha_habilitacion_boletin(entrega) == date(2026, 3, 22)


def test_rn10_cadena_completa_desde_el_cierre_de_unidad():
    cierre = date(2026, 4, 30)
    entrega = calcular_fecha_entrega_notas(cierre)
    habilitacion = calcular_fecha_habilitacion_boletin(entrega)
    assert entrega == date(2026, 5, 15)
    assert habilitacion == date(2026, 5, 22)
