"""RF-18: calcular la nota de unidad a partir de las calificaciones ya
registradas. La consume el boletín en PDF de la Fase 10 (frontend), por
curso — una inscripción tiene actividades de varios cursos a la vez en
la misma unidad, así que la función filtra también por `assignment`."""

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

    assert nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion) == Decimal(
        "80"
    )


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

    assert nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion) == Decimal(
        "30"
    )


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

    assert nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion) == Decimal(
        "75"
    )


@pytest.mark.django_db
def test_nota_de_unidad_no_mezcla_actividades_de_otro_curso():
    """Antes de este alcance la función no filtraba por `assignment`:
    sumaba actividades de todos los cursos de la unidad, no solo del
    curso pedido — el tope de 100 puntos (RN-01) es por curso."""
    asignacion_matematica = TeacherAssignmentFactory()
    asignacion_comunicacion = TeacherAssignmentFactory(
        section=asignacion_matematica.section, cycle=asignacion_matematica.cycle
    )
    unidad = GradingUnitFactory(cycle=asignacion_matematica.cycle)
    inscripcion = EnrollmentFactory(
        section=asignacion_matematica.section, cycle=asignacion_matematica.cycle
    )
    tipo = ActivityTypeFactory()

    actividad_matematica = ActivityFactory(
        assignment=asignacion_matematica, unit=unidad, activity_type=tipo, max_score=100
    )
    actividad_comunicacion = ActivityFactory(
        assignment=asignacion_comunicacion, unit=unidad, activity_type=tipo, max_score=100
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad_matematica,
        raw_score=70,
        current_score=70,
        recorded_by=asignacion_matematica.teacher,
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad_comunicacion,
        raw_score=90,
        current_score=90,
        recorded_by=asignacion_comunicacion.teacher,
    )

    assert nota_de_unidad(
        enrollment=inscripcion, unit=unidad, assignment=asignacion_matematica
    ) == Decimal("70")
    assert nota_de_unidad(
        enrollment=inscripcion, unit=unidad, assignment=asignacion_comunicacion
    ) == Decimal("90")
