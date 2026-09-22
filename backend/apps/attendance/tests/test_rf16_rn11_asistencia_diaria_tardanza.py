import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.attendance.models import Attendance
from apps.catalog.models import Course
from apps.catalog.tests.factories import SectionFactory
from apps.scheduling.models import TeacherAssignment
from apps.students.tests.factories import EnrollmentFactory


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    return UserFactory(role=rol)


@pytest.mark.django_db
def test_rf16_direccion_registra_presente_directamente():
    direccion = _direccion()
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/attendance/",
        {
            "enrollment": str(inscripcion.public_id),
            "date": "2026-01-13",
            "status": "presente",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["status"] == "presente"
    assert respuesta.data["source"] == Attendance.ORIGEN_MANUAL


@pytest.mark.django_db
def test_rn11_llegada_despues_del_corte_queda_tarde():
    direccion = _direccion()
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/attendance/",
        {
            "enrollment": str(inscripcion.public_id),
            "date": "2026-01-13",
            "check_in_time": "08:10:00",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["status"] == "tarde"


@pytest.mark.django_db
def test_rn11_llegada_antes_del_corte_queda_presente():
    direccion = _direccion()
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/attendance/",
        {
            "enrollment": str(inscripcion.public_id),
            "date": "2026-01-13",
            "check_in_time": "07:58:00",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["status"] == "presente"


@pytest.mark.django_db
def test_falta_mandar_estado_o_hora_de_llegada():
    direccion = _direccion()
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/attendance/",
        {"enrollment": str(inscripcion.public_id), "date": "2026-01-13"},
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_docente_registra_asistencia_de_su_propia_seccion_asignada():
    rol_docente = RoleFactory(name="Docente", permissions={"asistencia": "editar"})
    docente = UserFactory(role=rol_docente)
    seccion = SectionFactory(type="academica")
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
    TeacherAssignment.objects.create(
        teacher=docente, course=curso, section=seccion, cycle=seccion.cycle
    )
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/attendance/",
        {"enrollment": str(inscripcion.public_id), "date": "2026-01-13", "status": "presente"},
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_docente_no_puede_registrar_asistencia_de_una_seccion_ajena_acceso_no_autorizado():
    rol_docente = RoleFactory(name="Docente", permissions={"asistencia": "editar"})
    docente = UserFactory(role=rol_docente)
    seccion_ajena = SectionFactory(type="academica")
    inscripcion = EnrollmentFactory(section=seccion_ajena, cycle=seccion_ajena.cycle)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/attendance/",
        {"enrollment": str(inscripcion.public_id), "date": "2026-01-13", "status": "presente"},
        format="json",
    )

    assert respuesta.status_code == 403
    assert not Attendance.objects.exists()


@pytest.mark.django_db
def test_encargado_de_pagos_no_alcanza_asistencia_acceso_no_autorizado():
    rol = RoleFactory(name="Encargado de pagos", permissions={"asistencia": "sin_acceso"})
    pagos = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=pagos)

    respuesta = client.get("/api/v1/attendance/")
    assert respuesta.status_code == 403
