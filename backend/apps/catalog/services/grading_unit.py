from datetime import date

from ..domain.grading_unit import (
    UnidadInvalida,
    calcular_fecha_entrega_notas,
    calcular_fecha_habilitacion_boletin,
    validar_fechas_unidad,
)
from ..models import GradingUnit, SchoolCycle


def _validar(cycle: SchoolCycle, *, number: int, start_date: date, end_date: date, excluir=None):
    if not 1 <= number <= 4:
        raise UnidadInvalida("El número de unidad debe estar entre 1 y 4.")
    otras = GradingUnit.objects.filter(cycle=cycle, is_active=True)
    if excluir is not None:
        otras = otras.exclude(pk=excluir.pk)
    if otras.filter(number=number).exists():
        raise UnidadInvalida(f"El ciclo ya tiene la unidad {number}.")
    validar_fechas_unidad(
        start_date=start_date,
        end_date=end_date,
        cycle_start=cycle.start_date,
        cycle_end=cycle.end_date,
        otras=list(otras.values_list("start_date", "end_date")),
    )


def crear_unidad(
    *, cycle: SchoolCycle, number: int, start_date: date, end_date: date
) -> GradingUnit:
    _validar(cycle, number=number, start_date=start_date, end_date=end_date)
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
    _validar(unidad.cycle, number=number, start_date=start_date, end_date=end_date, excluir=unidad)
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
