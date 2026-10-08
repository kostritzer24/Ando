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
def test_rf16_la_asistencia_es_global_la_ve_cualquier_docente_de_la_seccion():
    """Decisión del dueño (oct 2026): la asistencia es una por estudiante y
    día, no por clase: la marque Dirección o un docente, los demás la ven."""
    direccion = _direccion()
    inscripcion = EnrollmentFactory()
    rol = RoleFactory(name="Docente", permissions={"asistencia": "ver"})
    docente = UserFactory(role=rol)
    curso = Course.objects.create(name="Matemática", type=Course.TIPO_ACADEMICO)
    TeacherAssignment.objects.create(
        teacher=docente,
        course=curso,
        section=inscripcion.section,
        cycle=inscripcion.section.cycle,
    )
    cliente_direccion = APIClient()
    cliente_direccion.force_authenticate(user=direccion)
    cliente_direccion.post(
        "/api/v1/attendance/",
        {"enrollment": str(inscripcion.public_id), "date": "2026-01-13", "status": "presente"},
        format="json",
    )

    cliente_docente = APIClient()
    cliente_docente.force_authenticate(user=docente)
    respuesta = cliente_docente.get(
        "/api/v1/attendance/", {"enrollment": str(inscripcion.public_id)}
    )

    assert respuesta.status_code == 200
    assert [a["date"] for a in respuesta.data["results"]] == ["2026-01-13"]


@pytest.mark.django_db
def test_rf16_la_hora_de_llegada_ya_no_existe_y_el_estado_tarde_se_rechaza():
    direccion = _direccion()
    inscripcion = EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/attendance/",
        {"enrollment": str(inscripcion.public_id), "date": "2026-01-13", "status": "tarde"},
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_falta_mandar_el_estado():
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


@pytest.mark.django_db
def test_rnf06_registrar_asistencia_deja_bitacora():
    from apps.core.models import AuditLog

    direccion = _direccion()
    client = APIClient()
    client.force_authenticate(user=direccion)

    client.post(
        "/api/v1/attendance/",
        {
            "enrollment": str(EnrollmentFactory().public_id),
            "date": "2026-01-13",
            "status": "ausente",
        },
        format="json",
    )

    registro = AuditLog.objects.get(entity_name="attendance.Attendance")
    assert registro.user == direccion
    assert registro.new_value["status"] == "ausente"


@pytest.mark.django_db
def test_rf16_registrar_dos_veces_el_mismo_dia_responde_400_no_500():
    """Hallazgo B-007: el doble clic rompía la restricción única con un 500."""
    direccion = _direccion()
    inscripcion = EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=direccion)
    datos = {"enrollment": str(inscripcion.public_id), "date": "2026-01-13", "status": "presente"}

    assert client.post("/api/v1/attendance/", datos, format="json").status_code == 201
    segunda = client.post("/api/v1/attendance/", datos, format="json")

    assert segunda.status_code == 400
    assert Attendance.objects.filter(enrollment=inscripcion).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("fecha", ["2099-01-05", "2026-01-10", "2026-01-11"])
def test_rf16_no_se_registra_asistencia_en_fecha_futura_ni_en_fin_de_semana(fecha):
    """Hallazgo B-004: sábado, domingo y fechas futuras ensuciaban los reportes."""
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/attendance/",
        {
            "enrollment": str(EnrollmentFactory().public_id),
            "date": fecha,
            "status": "presente",
        },
        format="json",
    )

    assert respuesta.status_code == 400
