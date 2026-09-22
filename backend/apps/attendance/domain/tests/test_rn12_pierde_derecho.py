from apps.attendance.domain.rights import pierde_derecho_a_actividades
from apps.attendance.models import Attendance


def test_rn12_ausente_sin_justificar_pierde_el_derecho():
    assert (
        pierde_derecho_a_actividades(Attendance.ESTADO_AUSENTE, tiene_justificacion_aprobada=False)
        is True
    )


def test_rn12_ausente_con_justificacion_aprobada_no_pierde_el_derecho():
    assert (
        pierde_derecho_a_actividades(Attendance.ESTADO_AUSENTE, tiene_justificacion_aprobada=True)
        is False
    )


def test_rn12_presente_nunca_pierde_el_derecho():
    assert (
        pierde_derecho_a_actividades(Attendance.ESTADO_PRESENTE, tiene_justificacion_aprobada=False)
        is False
    )


def test_rn12_tarde_no_pierde_el_derecho():
    assert (
        pierde_derecho_a_actividades(Attendance.ESTADO_TARDE, tiene_justificacion_aprobada=False)
        is False
    )
