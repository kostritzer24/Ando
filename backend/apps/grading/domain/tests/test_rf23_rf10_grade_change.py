from decimal import Decimal

import pytest

from apps.grading.domain.grade_change import (
    SolicitudDeModificacionInvalida,
    validar_resolucion,
    validar_solicitud,
)
from apps.grading.domain.unit_design import (
    DefinicionDeUnidadInvalida,
    validar_baja_de_actividad,
    validar_cambio_de_punteo_maximo,
)


def _solicitud(**cambios):
    datos = {
        "punteo_propuesto": Decimal("8"),
        "nota_vigente": Decimal("6"),
        "max_score": Decimal("10"),
        "hay_pendiente": False,
    }
    datos.update(cambios)
    validar_solicitud(**datos)


def test_rf23_una_solicitud_valida_pasa():
    _solicitud()


@pytest.mark.parametrize("propuesto", [Decimal("-1"), Decimal("10.01")])
def test_rf23_el_punteo_propuesto_respeta_el_maximo_de_la_actividad(propuesto):
    with pytest.raises(SolicitudDeModificacionInvalida):
        _solicitud(punteo_propuesto=propuesto)


def test_rf23_proponer_la_nota_vigente_no_es_una_correccion():
    with pytest.raises(SolicitudDeModificacionInvalida):
        _solicitud(punteo_propuesto=Decimal("6"))


def test_rf23_solo_una_solicitud_pendiente_por_nota():
    with pytest.raises(SolicitudDeModificacionInvalida):
        _solicitud(hay_pendiente=True)


def test_rf10_solo_se_resuelve_una_solicitud_pendiente():
    validar_resolucion(estado_actual="pendiente", estado_pendiente="pendiente")
    with pytest.raises(SolicitudDeModificacionInvalida):
        validar_resolucion(estado_actual="rechazada", estado_pendiente="pendiente")


def test_rn05_una_actividad_calificada_no_cambia_su_maximo_ni_se_da_de_baja():
    validar_cambio_de_punteo_maximo(tiene_notas=False)
    validar_baja_de_actividad(tiene_notas=False)
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_cambio_de_punteo_maximo(tiene_notas=True)
    with pytest.raises(DefinicionDeUnidadInvalida):
        validar_baja_de_actividad(tiene_notas=True)


def test_rn05_se_corrige_sin_autorizacion_hasta_el_dia_de_entrega_inclusive():
    from datetime import date

    from apps.grading.domain.grade_change import puede_corregirse_sin_autorizacion

    entrega = date(2026, 3, 15)
    assert puede_corregirse_sin_autorizacion(hoy=date(2026, 3, 15), fecha_entrega_notas=entrega)
    assert not puede_corregirse_sin_autorizacion(hoy=date(2026, 3, 16), fecha_entrega_notas=entrega)
