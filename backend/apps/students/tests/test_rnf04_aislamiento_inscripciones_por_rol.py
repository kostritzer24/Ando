import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Course
from apps.catalog.tests.factories import SchoolCycleFactory, SectionFactory
from apps.scheduling.models import TeacherAssignment
from apps.students.services.link import vincular_encargado_estudiante

from .factories import EnrollmentFactory, GuardianFactory, StudentFactory


@pytest.mark.django_db
def test_padre_de_familia_solo_ve_las_inscripciones_de_sus_propios_estudiantes():
    """GET /enrollments/ revela sección, ciclo y beca — sin este alcance,
    cualquier cuenta con `ver` en "estudiantes_encargados" (incluida una
    familia) vería la inscripción de cualquier estudiante del centro."""
    rol_familia = RoleFactory(
        name="Padre de familia", permissions={"estudiantes_encargados": "ver"}
    )
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)

    mi_hijo = StudentFactory(internal_code="ES001")
    hijo_ajeno = StudentFactory(internal_code="ES002")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")

    mi_inscripcion = EnrollmentFactory(student=mi_hijo)
    inscripcion_ajena = EnrollmentFactory(student=hijo_ajeno)

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.get("/api/v1/enrollments/")
    ids = {r["public_id"] for r in respuesta.data["results"]}

    assert ids == {str(mi_inscripcion.public_id)}

    respuesta_ajena = client.get(f"/api/v1/enrollments/{inscripcion_ajena.public_id}/")
    assert respuesta_ajena.status_code == 404


@pytest.mark.django_db
def test_docente_solo_ve_las_inscripciones_de_sus_propias_secciones_asignadas():
    rol_docente = RoleFactory(name="Docente", permissions={"estudiantes_encargados": "ver"})
    docente = UserFactory(role=rol_docente)

    ciclo = SchoolCycleFactory()
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
    mi_seccion = SectionFactory(cycle=ciclo, grade="Segundo básico")
    otra_seccion = SectionFactory(cycle=ciclo, grade="Tercero básico")
    TeacherAssignment.objects.create(teacher=docente, course=curso, section=mi_seccion, cycle=ciclo)

    mi_inscripcion = EnrollmentFactory(section=mi_seccion, cycle=ciclo)
    inscripcion_ajena = EnrollmentFactory(section=otra_seccion, cycle=ciclo)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/enrollments/")
    ids = {r["public_id"] for r in respuesta.data["results"]}

    assert ids == {str(mi_inscripcion.public_id)}
    assert str(inscripcion_ajena.public_id) not in ids
