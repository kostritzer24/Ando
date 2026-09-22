import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import SchoolCycleFactory, SectionFactory
from apps.scheduling.models import TeacherAssignment
from apps.students.services.link import vincular_encargado_estudiante

from .factories import EnrollmentFactory, GuardianFactory, StudentFactory


@pytest.mark.django_db
def test_padre_de_familia_solo_ve_a_sus_propios_estudiantes():
    rol_familia = RoleFactory(
        name="Padre de familia", permissions={"estudiantes_encargados": "ver"}
    )
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)

    mi_hijo = StudentFactory(internal_code="ES001")
    hijo_ajeno = StudentFactory(internal_code="ES002")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta_lista = client.get("/api/v1/students/")
    codigos = {r["internal_code"] for r in respuesta_lista.data["results"]}
    assert codigos == {"ES001"}

    respuesta_propio = client.get(f"/api/v1/students/{mi_hijo.public_id}/")
    assert respuesta_propio.status_code == 200

    respuesta_ajeno = client.get(f"/api/v1/students/{hijo_ajeno.public_id}/")
    assert respuesta_ajeno.status_code == 404


@pytest.mark.django_db
def test_docente_solo_ve_estudiantes_de_sus_propias_secciones_asignadas():
    rol_docente = RoleFactory(name="Docente", permissions={"estudiantes_encargados": "ver"})
    docente = UserFactory(role=rol_docente)

    ciclo = SchoolCycleFactory()
    curso = _crear_curso_academico()
    mi_seccion = SectionFactory(cycle=ciclo, grade="Segundo básico")
    otra_seccion = SectionFactory(cycle=ciclo, grade="Tercero básico")

    TeacherAssignment.objects.create(teacher=docente, course=curso, section=mi_seccion, cycle=ciclo)

    estudiante_en_mi_seccion = StudentFactory(internal_code="ES001")
    estudiante_en_otra_seccion = StudentFactory(internal_code="ES002")
    EnrollmentFactory(student=estudiante_en_mi_seccion, section=mi_seccion, cycle=ciclo)
    EnrollmentFactory(student=estudiante_en_otra_seccion, section=otra_seccion, cycle=ciclo)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/students/")
    codigos = {r["internal_code"] for r in respuesta.data["results"]}

    assert codigos == {"ES001"}


def _crear_curso_academico():
    from apps.catalog.models import Course

    return Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
