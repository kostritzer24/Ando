from decimal import Decimal

from django.utils import timezone

from ..models import Grade, GradeChangeRequest


class PunteoFueraDeRango(Exception):
    pass


def solicitar_modificacion(
    *, grade: Grade, requested_score: Decimal, reason: str, requested_by
) -> GradeChangeRequest:
    """RF-23 / RN-05. El punteo real (`grade.raw_score`) no se toca acá —
    solo se guarda la propuesta, pendiente de que Dirección la autorice."""
    if not (Decimal("0") <= requested_score <= grade.activity.max_score):
        raise PunteoFueraDeRango(
            f"El punteo propuesto debe estar entre 0 y {grade.activity.max_score}."
        )
    return GradeChangeRequest.objects.create(
        grade=grade,
        original_score=grade.raw_score,
        requested_score=requested_score,
        reason=reason,
        requested_by=requested_by,
    )


def resolver_modificacion(
    solicitud: GradeChangeRequest, *, aprobar: bool, authorized_by
) -> GradeChangeRequest:
    """RF-10 / RN-05. Aprobar cambia `Grade.current_score` (la que entra
    en los promedios y ve la familia) — `Grade.raw_score` nunca cambia."""
    solicitud.status = (
        GradeChangeRequest.ESTADO_APROBADA if aprobar else GradeChangeRequest.ESTADO_RECHAZADA
    )
    solicitud.authorized_by = authorized_by
    solicitud.decided_at = timezone.now()
    solicitud.save(update_fields=["status", "authorized_by", "decided_at", "updated_at"])

    if aprobar:
        grade = solicitud.grade
        grade.current_score = solicitud.requested_score
        grade.save(update_fields=["current_score", "updated_at"])

    return solicitud
