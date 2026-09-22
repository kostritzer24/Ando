from datetime import date

from apps.payments.domain.solvency import es_solvente, meses_del_periodo


def test_meses_del_periodo_incluye_ambos_extremos():
    assert meses_del_periodo(inicio=date(2026, 1, 15), hasta=date(2026, 3, 10)) == {
        (2026, 1),
        (2026, 2),
        (2026, 3),
    }


def test_meses_del_periodo_cruza_de_diciembre_a_enero():
    assert meses_del_periodo(inicio=date(2025, 11, 1), hasta=date(2026, 1, 1)) == {
        (2025, 11),
        (2025, 12),
        (2026, 1),
    }


def test_meses_del_periodo_hasta_anterior_a_inicio_da_vacio():
    assert meses_del_periodo(inicio=date(2026, 5, 1), hasta=date(2026, 1, 1)) == set()


def test_rn08_con_beca_siempre_es_solvente_aunque_no_haya_pagado_nada():
    assert es_solvente(tiene_beca=True, meses_esperados={(2026, 1), (2026, 2)}, meses_pagados=set())


def test_rn08_sin_beca_y_todos_los_meses_pagados_es_solvente():
    meses = {(2026, 1), (2026, 2)}
    assert es_solvente(tiene_beca=False, meses_esperados=meses, meses_pagados=meses) is True


def test_rn08_sin_beca_y_un_mes_pasado_sin_pagar_es_insolvente():
    assert (
        es_solvente(
            tiene_beca=False, meses_esperados={(2026, 1), (2026, 2)}, meses_pagados={(2026, 2)}
        )
        is False
    )
