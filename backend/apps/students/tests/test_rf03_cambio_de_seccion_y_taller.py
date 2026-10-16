import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Section
from apps.catalog.tests.factories import SchoolCycleFactory, SectionFactory
from apps.students.models import Enrollment
from apps.students.tests.factories import EnrollmentFactory, StudentFactory

pytestmark = pytest.mark.django_db


def _direccion_client():
    rol = RoleFactory(
        name="Dirección",
        permissions={"estudiantes_encargados": "editar", "datos_sensibles": "editar"},
    )
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))
    return client


def test_rf03_se_inscribe_a_un_estudiante_existente_en_un_taller_sin_duplicarlo():
    ciclo = SchoolCycleFactory()
    estudiante = StudentFactory()
    grado = SectionFactory(cycle=ciclo)
    taller = SectionFactory(cycle=ciclo, grade="Panadería", type=Section.TIPO_TALLER)
    EnrollmentFactory(student=estudiante, section=grado, cycle=ciclo)

    respuesta = _direccion_client().post(
        "/api/v1/enrollments/",
        {
            "student": str(estudiante.public_id),
            "section": str(taller.public_id),
            "cycle": str(ciclo.public_id),
            "enrolled_at": "2026-02-01",
        },
        format="json",
    )

    assert respuesta.status_code == 201, respuesta.data
    assert Enrollment.objects.filter(student=estudiante, is_active=True).count() == 2


def test_rf03_se_saca_a_un_estudiante_de_un_taller_y_se_puede_volver_a_meter():
    ciclo = SchoolCycleFactory()
    estudiante = StudentFactory()
    taller = SectionFactory(cycle=ciclo, grade="Panadería", type=Section.TIPO_TALLER)
    inscripcion = EnrollmentFactory(student=estudiante, section=taller, cycle=ciclo)
    client = _direccion_client()

    assert client.delete(f"/api/v1/enrollments/{inscripcion.public_id}/").status_code == 204
    de_nuevo = client.post(
        "/api/v1/enrollments/",
        {
            "student": str(estudiante.public_id),
            "section": str(taller.public_id),
            "cycle": str(ciclo.public_id),
            "enrolled_at": "2026-03-01",
        },
        format="json",
    )

    assert de_nuevo.status_code == 201, de_nuevo.data
    assert Enrollment.objects.filter(student=estudiante).count() == 1
    assert Enrollment.objects.get(student=estudiante).is_active is True


def test_rf03_cambiar_de_grado_mueve_la_misma_inscripcion():
    ciclo = SchoolCycleFactory()
    inscripcion = EnrollmentFactory(section=SectionFactory(cycle=ciclo, letter="A"), cycle=ciclo)
    otra = SectionFactory(cycle=ciclo, letter="B")

    respuesta = _direccion_client().patch(
        f"/api/v1/enrollments/{inscripcion.public_id}/",
        {"section": str(otra.public_id)},
        format="json",
    )

    assert respuesta.status_code == 200, respuesta.data
    inscripcion.refresh_from_db()
    assert inscripcion.section == otra
    assert Enrollment.objects.count() == 1


def test_rf03_no_se_puede_cambiar_un_grado_por_un_taller_ni_de_ciclo():
    ciclo = SchoolCycleFactory()
    inscripcion = EnrollmentFactory(section=SectionFactory(cycle=ciclo), cycle=ciclo)
    taller = SectionFactory(cycle=ciclo, grade="Panadería", type=Section.TIPO_TALLER)
    de_otro_ciclo = SectionFactory(cycle=SchoolCycleFactory())
    client = _direccion_client()
    url = f"/api/v1/enrollments/{inscripcion.public_id}/"

    assert client.patch(url, {"section": str(taller.public_id)}, format="json").status_code == 400
    assert (
        client.patch(url, {"section": str(de_otro_ciclo.public_id)}, format="json").status_code
        == 400
    )
