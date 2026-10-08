from datetime import date

import pytest

from apps.catalog.domain.grading_unit import UnidadInvalida, validar_fechas_unidad

CICLO = {"cycle_start": date(2026, 1, 15), "cycle_end": date(2026, 10, 30)}


def test_hu02_una_unidad_valida_dentro_del_ciclo_se_acepta():
    validar_fechas_unidad(
        start_date=date(2026, 1, 15), end_date=date(2026, 3, 31), otras=[], **CICLO
    )


def test_hu02_el_cierre_no_puede_ser_anterior_al_inicio():
    with pytest.raises(UnidadInvalida, match="anterior"):
        validar_fechas_unidad(
            start_date=date(2026, 5, 1), end_date=date(2026, 4, 1), otras=[], **CICLO
        )


def test_hu02_la_unidad_debe_caber_en_el_ciclo():
    with pytest.raises(UnidadInvalida, match="dentro del ciclo"):
        validar_fechas_unidad(
            start_date=date(2025, 12, 1), end_date=date(2026, 2, 1), otras=[], **CICLO
        )


def test_hu02_no_se_cruza_con_otra_unidad():
    with pytest.raises(UnidadInvalida, match="cruzan"):
        validar_fechas_unidad(
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 1),
            otras=[(date(2026, 1, 15), date(2026, 4, 15))],
            **CICLO,
        )
