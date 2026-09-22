from datetime import time

from apps.attendance.domain.late_arrival import calcular_estado_por_hora_llegada
from apps.attendance.models import Attendance


def test_rn11_llegada_a_las_ocho_en_punto_es_presente():
    assert calcular_estado_por_hora_llegada(time(8, 0)) == Attendance.ESTADO_PRESENTE


def test_rn11_llegada_exactamente_a_la_hora_de_corte_es_presente():
    assert calcular_estado_por_hora_llegada(time(8, 5)) == Attendance.ESTADO_PRESENTE


def test_rn11_un_minuto_despues_del_corte_es_tarde():
    assert calcular_estado_por_hora_llegada(time(8, 6)) == Attendance.ESTADO_TARDE


def test_rn11_mucho_despues_sigue_siendo_tarde():
    assert calcular_estado_por_hora_llegada(time(9, 30)) == Attendance.ESTADO_TARDE
