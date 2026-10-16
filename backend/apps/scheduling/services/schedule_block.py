from ..domain.day_structure import validar_periodo_para_seccion
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
        period_number=period_number,
        is_active=True,
        assignment__is_active=True,
        assignment__cycle=assignment.cycle,
    )
    if excluir is not None:
        vigentes = vigentes.exclude(pk=excluir.pk)

    if vigentes.filter(assignment__teacher=assignment.teacher).exists():
        raise CruceDeHorario(
            f"{assignment.teacher.nombre_completo()} ya tiene una clase asignada ese día "
            f"en el período {period_number}."
        )

    # Una sección tampoco puede tener dos cursos a la misma hora.
    if vigentes.filter(assignment__section=assignment.section).exists():
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
