"""RN-12: una falta sin justificar quita el derecho a las actividades
del día; la justificación se evalúa según el caso, nunca automática."""

from ..models import Attendance


def pierde_derecho_a_actividades(status: str, tiene_justificacion_aprobada: bool) -> bool:
    return status == Attendance.ESTADO_AUSENTE and not tiene_justificacion_aprobada
