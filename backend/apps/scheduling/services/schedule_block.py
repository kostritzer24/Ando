from ..domain.day_structure import horario_de_periodo
from ..models import ScheduleBlock, TeacherAssignment


class CruceDeHorario(Exception):
    pass


def crear_bloque(
    *, assignment: TeacherAssignment, day_of_week: str, period_number: int
) -> ScheduleBlock:
    """RF-06 / HU-06: rechaza cruces de docente y período. RN-13 se valida
    de paso, al pedir el horario del período (lanza si no existe)."""
    horario_de_periodo(period_number)

    hay_cruce = (
        ScheduleBlock.objects.filter(
            assignment__teacher=assignment.teacher,
            day_of_week=day_of_week,
            period_number=period_number,
            is_active=True,
        )
        .exclude(assignment=assignment)
        .exists()
    )
    if hay_cruce:
        raise CruceDeHorario(
            f"{assignment.teacher} ya tiene una clase asignada ese día "
            f"en el período {period_number}."
        )

    return ScheduleBlock.objects.create(
        assignment=assignment, day_of_week=day_of_week, period_number=period_number
    )
