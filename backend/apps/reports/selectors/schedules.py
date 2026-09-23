"""RF-15, reporte 4: horarios — el mismo horario que arma Dirección en
`/schedule-blocks/`, en forma de listado institucional."""

from apps.scheduling.models import ScheduleBlock


def resumen_horarios(*, section_id: str | None = None) -> list[dict]:
    bloques = ScheduleBlock.objects.filter(is_active=True).select_related(
        "assignment__course", "assignment__section", "assignment__teacher"
    )
    if section_id:
        bloques = bloques.filter(assignment__section__public_id=section_id)

    return [
        {
            "section": str(bloque.assignment.section),
            "course": bloque.assignment.course.name,
            "teacher": bloque.assignment.teacher.nombre_completo(),
            "day_of_week": bloque.day_of_week,
            "period_number": bloque.period_number,
        }
        for bloque in bloques.order_by(
            "assignment__section", "day_of_week", "period_number"
        )
    ]
