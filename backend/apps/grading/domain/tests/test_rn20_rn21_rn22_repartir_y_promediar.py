from decimal import Decimal

import pytest

from apps.grading.domain.scoring import calcular_nota_unidad
from apps.grading.domain.unit_design import (
    DefinicionDeUnidadInvalida,
    repartir_puntos,
    validar_actividad_calificable,
    validar_cambio_de_promedio,
    validar_nuevo_punteo_maximo,
    validar_promedio,
)


def test_rn20_tres_actividades_dejan_el_residuo_en_la_ultima():
    assert repartir_puntos([], 3) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]


def test_rn20_reparte_en_partes_exactas_cuando_alcanza():
    assert repartir_puntos([], 4) == [Decimal("25.00")] * 4


def test_rn20_las_calificadas_conservan_su_punteo_y_se_reparte_lo_que_sobra():
    partes = repartir_puntos([Decimal("10"), Decimal("10")], 3)

    assert partes == [Decimal("26.66"), Decimal("26.66"), Decimal("26.68")]
    assert sum(partes) + 20 == 100


def test_rn20_sin_actividades_libres_no_hay_reparto():
    with pytest.raises(DefinicionDeUnidadInvalida):
        repartir_puntos([Decimal("100")], 0)


def test_rn20_si_las_calificadas_ya_suman_100_no_queda_nada_que_repartir():
    with pytest.raises(DefinicionDeUnidadInvalida):
        repartir_puntos([Decimal("60"), Decimal("40")], 2)


def test_rn21_una_actividad_sin_punteo_maximo_no_se_califica():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_actividad_calificable(max_score=None, nombre="Proyecto")
    validar_actividad_calificable(max_score=Decimal("10"), nombre="Proyecto")


def test_rn21_una_actividad_sin_punteo_no_suma_al_tope_de_100():
    validar_nuevo_punteo_maximo(Decimal("100"), None)


def test_rn22_la_unidad_promediada_lleva_lo_obtenido_a_100():
    # 49 de 70 evaluados = 70 sobre 100.
    assert calcular_nota_unidad(
        [Decimal("9"), Decimal("40")], puntos_evaluados=Decimal("70")
    ) == Decimal("70.00")


def test_rn22_redondea_a_dos_decimales_mitad_hacia_arriba():
    # 2 de 3 = 66.666… → 66.67
    assert calcular_nota_unidad([Decimal("2")], puntos_evaluados=Decimal("3")) == Decimal("66.67")


def test_rn22_sin_promedio_la_nota_sigue_siendo_la_suma():
    assert calcular_nota_unidad([Decimal("9"), Decimal("40")]) == Decimal("49")


def test_rn22_sin_puntos_evaluados_la_nota_es_cero():
    assert calcular_nota_unidad([], puntos_evaluados=Decimal("0")) == Decimal("0.00")


def test_rn22_no_se_cambia_el_promedio_con_un_boletin_aprobado():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_cambio_de_promedio(hay_boletin_aprobado=True)
    validar_cambio_de_promedio(hay_boletin_aprobado=False)


def test_rn22_no_se_promedia_una_unidad_sin_puntos():
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_promedio(puntos_evaluados=Decimal("0"))
