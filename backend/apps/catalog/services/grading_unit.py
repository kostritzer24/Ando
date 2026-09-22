from datetime import date

from ..domain.grading_unit import calcular_fecha_entrega_notas, calcular_fecha_habilitacion_boletin
from ..models import GradingUnit, SchoolCycle


def crear_unidad(
    *, cycle: SchoolCycle, number: int, start_date: date, end_date: date
) -> GradingUnit:
    grades_due_date = calcular_fecha_entrega_notas(end_date)
    report_card_enabled_date = calcular_fecha_habilitacion_boletin(grades_due_date)
    return GradingUnit.objects.create(
        cycle=cycle,
        number=number,
        start_date=start_date,
        end_date=end_date,
        grades_due_date=grades_due_date,
        report_card_enabled_date=report_card_enabled_date,
    )


def actualizar_unidad(
    unidad: GradingUnit, *, number: int, start_date: date, end_date: date
) -> GradingUnit:
    unidad.number = number
    unidad.start_date = start_date
    unidad.end_date = end_date
    unidad.grades_due_date = calcular_fecha_entrega_notas(end_date)
    unidad.report_card_enabled_date = calcular_fecha_habilitacion_boletin(unidad.grades_due_date)
    unidad.save(
        update_fields=[
            "number",
            "start_date",
            "end_date",
            "grades_due_date",
            "report_card_enabled_date",
            "updated_at",
        ]
    )
    return unidad
