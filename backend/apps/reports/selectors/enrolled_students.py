"""RF-15, reporte 5: estudiantes inscritos."""

from apps.students.models import Enrollment


def estudiantes_inscritos(
    *, cycle_id: str | None = None, section_id: str | None = None
) -> list[dict]:
    inscripciones = Enrollment.objects.filter(is_active=True).select_related(
        "student", "section", "cycle", "scholarship"
    )
    if cycle_id:
        inscripciones = inscripciones.filter(cycle__public_id=cycle_id)
    if section_id:
        inscripciones = inscripciones.filter(section__public_id=section_id)

    return [
        {
            "student_code": inscripcion.student.internal_code,
            "student_name": inscripcion.student.nombre_completo(),
            "section": str(inscripcion.section),
            "cycle": inscripcion.cycle.year,
            "status": inscripcion.get_status_display(),
            "scholarship": inscripcion.scholarship.name if inscripcion.scholarship_id else "",
        }
        for inscripcion in inscripciones.order_by(
            "section__grade", "section__letter", "student__last_name"
        )
    ]
