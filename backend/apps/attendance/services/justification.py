from django.utils import timezone

from ..models import Attendance, Justification


def crear_justificacion(
    *,
    attendance: Attendance,
    justification_type,
    submitted_by,
    reason_detail: str = "",
    supporting_document=None,
) -> Justification:
    """RF-12."""
    return Justification.objects.create(
        attendance=attendance,
        justification_type=justification_type,
        reason_detail=reason_detail,
        supporting_document=supporting_document,
        submitted_by=submitted_by,
    )


def resolver_justificacion(
    justificacion: Justification, *, aprobar: bool, resolved_by
) -> Justification:
    """RN-12: la resolución evalúa cada caso — nunca es automática. Una
    justificación aprobada cambia la asistencia a 'justificado'."""
    justificacion.resolution = (
        Justification.RESOLUCION_APROBADA if aprobar else Justification.RESOLUCION_RECHAZADA
    )
    justificacion.resolved_by = resolved_by
    justificacion.resolved_at = timezone.now()
    justificacion.save(update_fields=["resolution", "resolved_by", "resolved_at", "updated_at"])

    if aprobar:
        asistencia = justificacion.attendance
        asistencia.status = Attendance.ESTADO_JUSTIFICADO
        asistencia.save(update_fields=["status", "updated_at"])

    return justificacion
