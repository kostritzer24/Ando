import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.attendance.models import Attendance, Justification
from apps.catalog.models import JustificationType

from .factories import AttendanceFactory


@pytest.mark.django_db
def test_rf12_direccion_registra_una_justificacion():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Constancia médica", requires_document=True)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/justifications/",
        {
            "attendance": str(asistencia.public_id),
            "justification_type": str(tipo.public_id),
            "reason_detail": "Consulta médica de emergencia.",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["resolution"] == Justification.RESOLUCION_PENDIENTE


@pytest.mark.django_db
def test_rn12_aprobar_la_justificacion_cambia_la_asistencia_a_justificado():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Motivo familiar")

    client = APIClient()
    client.force_authenticate(user=direccion)

    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )
    justificacion_id = creada.data["public_id"]

    respuesta = client.post(
        f"/api/v1/justifications/{justificacion_id}/resolve/", {"aprobar": True}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["resolution"] == Justification.RESOLUCION_APROBADA
    asistencia.refresh_from_db()
    assert asistencia.status == Attendance.ESTADO_JUSTIFICADO


@pytest.mark.django_db
def test_rechazar_la_justificacion_no_cambia_la_asistencia():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Motivo familiar")

    client = APIClient()
    client.force_authenticate(user=direccion)

    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )
    justificacion_id = creada.data["public_id"]

    respuesta = client.post(
        f"/api/v1/justifications/{justificacion_id}/resolve/", {"aprobar": False}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["resolution"] == Justification.RESOLUCION_RECHAZADA
    asistencia.refresh_from_db()
    assert asistencia.status == Attendance.ESTADO_AUSENTE


@pytest.mark.django_db
def test_solo_direccion_resuelve_justificaciones_acceso_no_autorizado():
    rol_guia = RoleFactory(name="Docente con sección a cargo", permissions={"asistencia": "editar"})
    guia = UserFactory(role=rol_guia)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Motivo familiar")

    client = APIClient()
    client.force_authenticate(user=guia)

    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )
    assert creada.status_code == 201
    justificacion_id = creada.data["public_id"]

    respuesta = client.post(
        f"/api/v1/justifications/{justificacion_id}/resolve/", {"aprobar": True}, format="json"
    )

    assert respuesta.status_code == 403
    asistencia.refresh_from_db()
    assert asistencia.status == Attendance.ESTADO_AUSENTE
