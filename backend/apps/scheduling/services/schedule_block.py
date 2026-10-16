from ..domain.day_structure import (
    jornada_de_grado,
    periodos_se_cruzan,
    validar_periodo_para_seccion,
)
from ..models import ScheduleBlock, TeacherAssignment


class CruceDeHorario(Exception):
    pass


def validar_bloque(
    *,
    assignment: TeacherAssignment,
    day_of_week: str,
    period_number: int,
    excluir: ScheduleBlock | None = None,
) -> None:
    """RF-06 / HU-06: rechaza cruces de docente y de sección. RN-13 se
    valida de paso (período existente y de la franja que corresponde).

    Solo cuentan los bloques vigentes de asignaciones vigentes del mismo
    ciclo: un bloque de una asignación dada de baja no ocupa la celda."""
    validar_periodo_para_seccion(period_number, assignment.section.type == "taller")

    vigentes = ScheduleBlock.objects.filter(
        day_of_week=day_of_week,
        is_active=True,
        assignment__is_active=True,
        assignment__cycle=assignment.cycle,
    ).select_related("assignment__section")
    if excluir is not None:
        vigentes = vigentes.exclude(pk=excluir.pk)

    # Dos horarios (básicos y bachillerato) con el receso en lugar distinto:
    # el choque se mide por la hora real, no por el número de período.
    jornada = jornada_de_grado(assignment.section.grade)
    for otro in vigentes.filter(assignment__teacher=assignment.teacher):
        jornada_otro = jornada_de_grado(otro.assignment.section.grade)
        if periodos_se_cruzan(period_number, jornada, otro.period_number, jornada_otro):
            raise CruceDeHorario(
                f"{assignment.teacher.nombre_completo()} ya tiene una clase asignada ese día "
                f"a esa hora ({otro.assignment.section}, período {otro.period_number})."
            )

    # Una sección tampoco puede tener dos cursos a la misma hora.
    if vigentes.filter(
        assignment__section=assignment.section, period_number=period_number
    ).exists():
        raise CruceDeHorario(
            f"La sección {assignment.section} ya tiene otro curso ese día en el período "
            f"{period_number}."
        )


def crear_bloque(
    *, assignment: TeacherAssignment, day_of_week: str, period_number: int
) -> ScheduleBlock:
    validar_bloque(assignment=assignment, day_of_week=day_of_week, period_number=period_number)

    # Un bloque dado de baja antes se reactiva en lugar de chocar con la
    # restricción de unicidad.
    previo = ScheduleBlock.objects.filter(
        assignment=assignment, day_of_week=day_of_week, period_number=period_number
    ).first()
    if previo is not None:
        previo.is_active = True
        previo.save(update_fields=["is_active", "updated_at"])
        return previo
    return ScheduleBlock.objects.create(
        assignment=assignment, day_of_week=day_of_week, period_number=period_number
    )
