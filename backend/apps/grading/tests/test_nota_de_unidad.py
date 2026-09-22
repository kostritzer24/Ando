"""RF-18: calcular la nota de unidad a partir de las calificaciones ya
registradas. Todavía no tiene un endpoint propio — lo va a consumir el
boletín de la Fase 9 — pero la función ya es parte del alcance de esta
fase y se prueba directamente."""

from decimal import Decimal

import pytest

from apps.catalog.tests.factories import GradingUnitFactory
from apps.grading.models import Grade
from apps.grading.services.grade import nota_de_unidad
from apps.students.tests.factories import EnrollmentFactory

from .factories import ActivityFactory, ActivityTypeFactory, TeacherAssignmentFactory


@pytest.mark.django_db
def test_nota_de_unidad_suma_las_calificaciones_vigentes():
    asignacion = TeacherAssignmentFactory()
    unidad = GradingUnitFactory(cycle=asignacion.cycle)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    tipo = ActivityTypeFactory()

    actividad_uno = ActivityFactory(
        assignment=asignacion, unit=unidad, activity_type=tipo, max_score=40
    )
    actividad_dos = ActivityFactory(
        assignment=asignacion, unit=unidad, activity_type=tipo, max_score=60
    )

    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad_uno,
        raw_score=30,
        current_score=30,
        recorded_by=asignacion.teacher,
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad_dos,
        raw_score=50,
        current_score=50,
        recorded_by=asignacion.teacher,
    )

    assert nota_de_unidad(enrollment=inscripcion, unit=unidad) == Decimal("80")


@pytest.mark.django_db
def test_nota_de_unidad_parcial_sin_todas_las_actividades_calificadas():
    asignacion = TeacherAssignmentFactory()
    unidad = GradingUnitFactory(cycle=asignacion.cycle)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    tipo = ActivityTypeFactory()

    actividad_uno = ActivityFactory(
        assignment=asignacion, unit=unidad, activity_type=tipo, max_score=40
    )
    ActivityFactory(assignment=asignacion, unit=unidad, activity_type=tipo, max_score=60)

    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad_uno,
        raw_score=30,
        current_score=30,
        recorded_by=asignacion.teacher,
    )

    assert nota_de_unidad(enrollment=inscripcion, unit=unidad) == Decimal("30")


@pytest.mark.django_db
def test_nota_de_unidad_usa_current_score_no_raw_score():
    """RN-06: la nota de unidad se calcula con la nota vigente, la que
    entra en los promedios — nunca con el punteo real original si ya
    hubo una modificación aprobada."""
    asignacion = TeacherAssignmentFactory()
    unidad = GradingUnitFactory(cycle=asignacion.cycle)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    actividad = ActivityFactory(
        assignment=asignacion, unit=unidad, activity_type=ActivityTypeFactory(), max_score=100
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=60,
        current_score=75,
        recorded_by=asignacion.teacher,
    )

    assert nota_de_unidad(enrollment=inscripcion, unit=unidad) == Decimal("75")
