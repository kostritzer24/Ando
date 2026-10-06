from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.services import registrar_cambio

from ..domain.grade_change import validar_resolucion, validar_solicitud
from ..models import Grade, GradeChangeRequest

ENTIDAD_SOLICITUD = "grading.GradeChangeRequest"
ENTIDAD_NOTA = "grading.Grade"


def hay_solicitud_pendiente(grade: Grade) -> bool:
    return GradeChangeRequest.objects.filter(
        grade=grade, status=GradeChangeRequest.ESTADO_PENDIENTE, is_active=True
    ).exists()


@transaction.atomic
def solicitar_modificacion(
    *, grade: Grade, requested_score: Decimal, reason: str, requested_by
) -> GradeChangeRequest:
    """RF-23 / RN-05. El punteo real (`grade.raw_score`) no se toca acá —
    solo se guarda la propuesta, pendiente de que Dirección la autorice.
    `original_score` es la nota vigente al pedir el cambio: es contra la
    que Dirección decide, y después de una primera corrección ya no es el
    punteo real."""
    grade = Grade.objects.select_for_update().select_related("activity").get(pk=grade.pk)
    validar_solicitud(
        punteo_propuesto=requested_score,
        nota_vigente=grade.current_score,
        max_score=grade.activity.max_score,
        hay_pendiente=hay_solicitud_pendiente(grade),
    )
    solicitud = GradeChangeRequest.objects.create(
        grade=grade,
        original_score=grade.current_score,
        requested_score=requested_score,
        reason=reason,
        requested_by=requested_by,
    )
    registrar_cambio(
        usuario=requested_by,
        entidad_nombre=ENTIDAD_SOLICITUD,
        entidad_id=solicitud.id,
        accion="crear",
        valor_nuevo={
            "grade": str(grade.public_id),
            "original_score": str(solicitud.original_score),
            "requested_score": str(requested_score),
            "reason": reason,
        },
    )
    return solicitud


@transaction.atomic
def resolver_modificacion(
    solicitud: GradeChangeRequest, *, aprobar: bool, authorized_by
) -> GradeChangeRequest:
    """RF-10 / RN-05. Aprobar cambia `Grade.current_score` (la que entra
    en los promedios y ve la familia) — `Grade.raw_score` nunca cambia.
    Se bloquea la fila para que dos decisiones simultáneas no pasen las
    dos por "pendiente"."""
    solicitud = GradeChangeRequest.objects.select_for_update().get(pk=solicitud.pk)
    validar_resolucion(
        estado_actual=solicitud.status, estado_pendiente=GradeChangeRequest.ESTADO_PENDIENTE
    )
    solicitud.status = (
        GradeChangeRequest.ESTADO_APROBADA if aprobar else GradeChangeRequest.ESTADO_RECHAZADA
    )
    solicitud.authorized_by = authorized_by
    solicitud.decided_at = timezone.now()
    solicitud.save(update_fields=["status", "authorized_by", "decided_at", "updated_at"])
    registrar_cambio(
        usuario=authorized_by,
        entidad_nombre=ENTIDAD_SOLICITUD,
        entidad_id=solicitud.id,
        accion="actualizar",
        valor_anterior={"status": GradeChangeRequest.ESTADO_PENDIENTE},
        valor_nuevo={"status": solicitud.status},
    )

    if aprobar:
        grade = Grade.objects.select_for_update().get(pk=solicitud.grade_id)
        anterior = grade.current_score
        grade.current_score = solicitud.requested_score
        grade.save(update_fields=["current_score", "updated_at"])
        registrar_cambio(
            usuario=authorized_by,
            entidad_nombre=ENTIDAD_NOTA,
            entidad_id=grade.id,
            accion="actualizar",
            valor_anterior={"current_score": str(anterior)},
            valor_nuevo={"current_score": str(grade.current_score)},
        )

    return solicitud
