import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Course
from apps.catalog.tests.factories import SectionFactory
from apps.scheduling.models import TeacherAssignment
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

from .factories import AttendanceFactory


@pytest.mark.django_db
def test_padre_de_familia_solo_ve_la_asistencia_de_su_propio_estudiante():
    rol_familia = RoleFactory(name="Padre de familia", permissions={"asistencia": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)

    mi_hijo = StudentFactory(internal_code="ES001")
    hijo_ajeno = StudentFactory(internal_code="ES002")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")

    mi_inscripcion = EnrollmentFactory(student=mi_hijo)
    inscripcion_ajena = EnrollmentFactory(student=hijo_ajeno)
    AttendanceFactory(enrollment=mi_inscripcion)
    AttendanceFactory(enrollment=inscripcion_ajena)

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.get("/api/v1/attendance/")

    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_docente_solo_ve_la_asistencia_de_sus_secciones_asignadas():
    rol_docente = RoleFactory(name="Docente", permissions={"asistencia": "ver"})
    docente = UserFactory(role=rol_docente)

    mi_seccion = SectionFactory(type="academica")
    otra_seccion = SectionFactory(type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
    TeacherAssignment.objects.create(
        teacher=docente, course=curso, section=mi_seccion, cycle=mi_seccion.cycle
    )

    inscripcion_propia = EnrollmentFactory(section=mi_seccion, cycle=mi_seccion.cycle)
    inscripcion_ajena = EnrollmentFactory(section=otra_seccion, cycle=otra_seccion.cycle)
    AttendanceFactory(enrollment=inscripcion_propia)
    AttendanceFactory(enrollment=inscripcion_ajena)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/attendance/")

    assert respuesta.data["count"] == 1
