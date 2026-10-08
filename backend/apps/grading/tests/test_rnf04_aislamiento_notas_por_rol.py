import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.grading.models import Grade
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

from .factories import ActivityFactory, TeacherAssignmentFactory


@pytest.mark.django_db
def test_padre_de_familia_solo_ve_las_notas_de_su_propio_estudiante():
    rol_familia = RoleFactory(name="Padre de familia", permissions={"notas": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)

    mi_hijo = StudentFactory(internal_code="ES001")
    hijo_ajeno = StudentFactory(internal_code="ES002")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")

    asignacion = TeacherAssignmentFactory()
    actividad = ActivityFactory(assignment=asignacion)
    mi_inscripcion = EnrollmentFactory(
        student=mi_hijo, section=asignacion.section, cycle=asignacion.cycle
    )
    inscripcion_ajena = EnrollmentFactory(
        student=hijo_ajeno, section=asignacion.section, cycle=asignacion.cycle
    )
    Grade.objects.create(
        enrollment=mi_inscripcion,
        activity=actividad,
        raw_score=8,
        current_score=8,
        recorded_by=asignacion.teacher,
    )
    Grade.objects.create(
        enrollment=inscripcion_ajena,
        activity=actividad,
        raw_score=9,
        current_score=9,
        recorded_by=asignacion.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.get("/api/v1/grades/")

    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_docente_solo_ve_las_notas_de_sus_propias_asignaciones():
    rol_docente = RoleFactory(name="Docente", permissions={"notas": "ver"})
    docente = UserFactory(role=rol_docente)
    mi_asignacion = TeacherAssignmentFactory(teacher=docente)
    otra_asignacion = TeacherAssignmentFactory()

    mi_actividad = ActivityFactory(assignment=mi_asignacion)
    otra_actividad = ActivityFactory(assignment=otra_asignacion)

    mi_inscripcion = EnrollmentFactory(section=mi_asignacion.section, cycle=mi_asignacion.cycle)
    otra_inscripcion = EnrollmentFactory(
        section=otra_asignacion.section, cycle=otra_asignacion.cycle
    )
    Grade.objects.create(
        enrollment=mi_inscripcion,
        activity=mi_actividad,
        raw_score=8,
        current_score=8,
        recorded_by=docente,
    )
    Grade.objects.create(
        enrollment=otra_inscripcion,
        activity=otra_actividad,
        raw_score=9,
        current_score=9,
        recorded_by=otra_asignacion.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/grades/")

    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_tallerista_no_alcanza_notas_de_ningun_tipo_acceso_no_autorizado():
    """ADR-0001: TALL nunca alcanza Notas, ni siquiera de su propio
    taller — los talleres no generan calificaciones."""
    rol = RoleFactory(name="Tallerista", permissions={"notas": "sin_acceso"})
    tallerista = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=tallerista)

    respuesta = client.get("/api/v1/grades/")
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_rn06_la_familia_ve_solo_la_nota_total_sin_detalle_de_actividad_ni_docente():
    """Decisión del dueño (oct 2026): la familia ve la nota por curso y unidad."""
    rol_familia = RoleFactory(name="Padre de familia", permissions={"notas": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)
    hijo = StudentFactory()
    vincular_encargado_estudiante(guardian=encargado, student=hijo, relationship="Madre")
    asignacion = TeacherAssignmentFactory()
    inscripcion = EnrollmentFactory(
        student=hijo, section=asignacion.section, cycle=asignacion.cycle
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=ActivityFactory(assignment=asignacion),
        raw_score=8,
        current_score=8,
        recorded_by=asignacion.teacher,
    )
    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    fila = client.get("/api/v1/grades/").data["results"][0]

    assert fila["current_score"] is not None
    assert {"course_name", "unit_number"} <= set(fila)
    assert not {"recorded_by", "activity_name", "max_score", "raw_score"} & set(fila)
