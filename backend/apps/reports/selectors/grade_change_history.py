"""RF-15, reporte 6: historial de modificaciones de notas (RF-10/RF-23)."""

from apps.grading.models import GradeChangeRequest


def historial_modificaciones(
    *, cycle_id: str | None = None, section_id: str | None = None, unit_id: str | None = None
) -> list[dict]:
    solicitudes = GradeChangeRequest.objects.filter(is_active=True).select_related(
        "grade__enrollment__student",
        "grade__enrollment__section",
        "grade__activity__assignment__course",
        "grade__activity__unit",
        "requested_by",
        "authorized_by",
    )
    if cycle_id:
        solicitudes = solicitudes.filter(grade__enrollment__cycle__public_id=cycle_id)
    if section_id:
        solicitudes = solicitudes.filter(grade__enrollment__section__public_id=section_id)
    if unit_id:
        solicitudes = solicitudes.filter(grade__activity__unit__public_id=unit_id)

    return [
        {
            "student_code": s.grade.enrollment.student.internal_code,
            "student_name": s.grade.enrollment.student.nombre_completo(),
            "course": s.grade.activity.assignment.course.name,
            "unit": s.grade.activity.unit.number,
            "original_score": s.original_score,
            "requested_score": s.requested_score,
            "reason": s.reason,
            "requested_by": s.requested_by.username,
            "status": s.get_status_display(),
            "authorized_by": s.authorized_by.username if s.authorized_by_id else "",
            "decided_at": s.decided_at,
        }
        for s in solicitudes.order_by("-created_at")
    ]
