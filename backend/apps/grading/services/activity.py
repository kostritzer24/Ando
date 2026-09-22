from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.catalog.models import ActivityType, Course, GradingUnit
from apps.scheduling.models import TeacherAssignment

from ..domain.unit_design import validar_nuevo_punteo_maximo
from ..models import Activity


class AsignacionNoCalifica(Exception):
    pass


def _validar_asignacion_califica(assignment: TeacherAssignment) -> None:
    """ADR-0001, consecuencias: no se puede crear Actividad sobre una
    Asignación docente de un curso de tipo 'taller' — los talleres no
    generan calificaciones."""
    if assignment.course.type != Course.TIPO_ACADEMICO:
        raise AsignacionNoCalifica(
            "No se pueden definir actividades para un curso de taller (ADR-0001)."
        )


def crear_actividad(
    *,
    assignment: TeacherAssignment,
    unit: GradingUnit,
    activity_type: ActivityType,
    name: str,
    max_score: Decimal,
    due_date: date,
) -> Activity:
    _validar_asignacion_califica(assignment)
    suma_actual = Activity.objects.filter(
        assignment=assignment, unit=unit, is_active=True
    ).aggregate(total=Sum("max_score"))["total"] or Decimal("0")
    validar_nuevo_punteo_maximo(suma_actual, max_score)
    return Activity.objects.create(
        assignment=assignment,
        unit=unit,
        activity_type=activity_type,
        name=name,
        max_score=max_score,
        due_date=due_date,
    )
